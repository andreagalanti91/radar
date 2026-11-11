# W2 + MACD · robustezza statistica (10–11/11/2026)

Domanda: quanto di "10k → ~119k dal 2021, 14 trade, WR 93%, DD −22,7%" è vantaggio reale? Preregistrazione in `PREREG.md`.
Regole identiche a `radar/weekly.py` (importato, costanti variate solo in memoria). 10.000 $ a 1x, costi inclusi.
Base riprodotta: 118.628 $, 14 trade, WR 92,9%, DD −22,7%, MAR 47,9. Buy & hold 25.695 $, DD −76,6%.

**Verdetto: MISTA (3 prove su 5 reggono).** Solido: il vantaggio sul buy & hold e la forma della regola. Fragile: i numeri
di facciata (119k, WR 93%, DD −22,7%), la protezione dal 2018 e la scelta dei parametri fuori dal 2021–26.

| Prova | Soglia preregistrata | Esito |
|---|---|---|
| 1 Selezione (DSR) | DSR ≥ 0,95 con N ~150 | regge (0,99), con riserva |
| 2 Storia 2015–20 | MAR ≥ B&H e 2018 ≥ −25% | parziale: MAR no, 2018 dipende dalla data di partenza |
| 3 Trade | P(WR<70%) < 10%, top 3 < 60%, mai sotto B&H | regge |
| 4 Vicini | ≥ 70% sopra metà MAR, base ≤ 80° percentile | regge al limite (78%, 80° percentile) |
| 5 Walk-forward | ≥ 50% del log-rendimento, DD entro 10 punti | non regge (69%, ma DD −38,7 contro −22,7) |

## 1 · Selezione
Prove sugli stessi dati prima di arrivare a W2 + F1: ~170 dirette (W1 33, W2 30, W5, 31 del DSR, uscite 11, size 4, F1 54,
portafoglio 18, giri orari) e ~900 con la mappa delle 649 regole. F1 è stato aggiunto dopo aver guardato i trade persi.
Sharpe settimanale annualizzato 1,33 (306 settimane).

| Varianza fra prove | N | Sharpe atteso dal caso | Sharpe netto | Haircut | DSR |
|---|---|---|---|---|---|
| vicini | 150 | 0,28 | 1,05 | 21% | 0,998 |
| larga | 150 | 0,47 | 0,86 | 35% | 0,991 |
| larga | 900 | 0,57 | 0,76 | 43% | 0,982 |

Riserva: il DSR tratta 306 settimane come indipendenti, ma i trade sono 14. La misura più onesta della selezione è la
regola prima di F1: 69.285 $, WR 68%, DD −42,6%. F1 vale +49k in campione; fuori campione (2018–20) porta il MAR da 0,14 a 2,44.

## 2 · Storia lunga (pseudo fuori campione)
Dati Bitstamp 2014→08/2017, Binance spot fino a 08/2019, poi repo. Proxy: flusso = CVD spot z dal 27/11/2017 al 04/2020
(prima non esiste: la versione "con flusso" resta ferma fino a fine 2017); funding 0 prima del 2020, quindi niente uscita
su distribuzione. Una simulazione continua dal 2015. Celle: rendimento % / DD % (trade).

| Versione | 2015–17 toro | 2018 orso | 2019–20 | 2015–20 | MAR 15–20 |
|---|---|---|---|---|---|
| flusso + F1 (in uso) | +18 / −30 (3) | −14 / −48 (2) | +225 / −33 (6) | +221 / −50 | 4,4 |
| flusso, senza F1 | +18 / −30 (3) | −54 / −72 (5) | +208 / −47 (7) | +63 / −73 | 0,9 |
| senza flusso, F1 | +565 / −39 (19) | −16 / −48 (2) | +196 / −61 (10) | +1.506 / −61 | 24,7 |
| senza flusso né F1 | +1.784 / −43 (19) | −55 / −72 (5) | +163 / −65 (11) | +2.068 / −74 | 28,1 |
| buy & hold | +4.271 / −46 | −72 / −81 | +662 / −63 | +9.117 / −83 | 109,6 |

- Nel toro 2015–17 e nel 2019–20 la regola rende molto meno del B&H (WR 55–58% senza flusso). Batte il B&H solo
  includendo un bear: 2018–20 +178% contro +116%, DD −48% contro −81%.
- Il 2018 NON costa −18%: partendo flat il 01/01/2018 la regola compra il 07/01 a 16.150 $ (MACD ancora sopra il segnale)
  e perde **−41% in un solo trade** (stop iniziale 2,5 ATRw = 40,6% del prezzo). Anno −33%, DD −48%. F1 ferma i rientri
  successivi, non il primo ingresso sul top. I long non hanno tetto di rischio (gli short sì, 25%).
- Con MACD 10/24/7 o 12/26/9 (identici a 8/21/5 nel 2021–26) il 2018 fa −52%, DD −63%: la protezione dipende dal parametro.
- WR 2018–20: 6/9. La simulazione continua dà 133.734 $ dal 2021 (13 trade): la partenza flat al 01/01/2021 sposta il finale del 13%.

## 3 · Trade dal 2021
| Misura | Valore |
|---|---|
| Bootstrap trade (10.000): CAGR 5° / 50° / 95° percentile | 30% / 52% / 82% (finale 46k / 116k / 330k) |
| P(finale sotto il B&H) | 0,2% |
| P(WR vero < 70%), 13/14 | 3,5% (limite inferiore 95%: 66%) |
| P(WR < 70%) con il 2018–20 (19/23) | 11% |
| WR senza F1 | 13/19 = 68% |
| 3 trade migliori | 51% del log-rendimento; senza: 33.483 $ |
| Togliendo un trade | peggior caso 66.894 $ (senza 01/2021 +77%); mai sotto il B&H |
| Log-rendimento per anno d'ingresso | 2021 43%, 2023 19%, 2024 25%, 2025–26 10% |
| Block bootstrap settimanale: CAGR 5° / 50° / 95° | 18% / 48% / 93% (B&H −24% / 14% / 68%) |
| Block bootstrap: DD mediano / 5° percentile | −29% / −45%; P(DD oltre −30%) 45%, oltre −40%) 12% |
| P(batte il B&H) / P(Calmar migliore) | 90% / 97% |
| Sott'acqua | 94% dei giorni sotto il massimo, periodo più lungo 290 giorni (B&H 846), 31% dei giorni oltre −10% |

Il bootstrap dei trade sottostima il DD: il campione contiene una sola perdita (−4,1%), quindi non può generarne di peggiori.
Il DD −22,7% storico è sotto la mediana del block bootstrap (−29%).

## 4 · Vicini (50 configurazioni, un fattore o una coppia alla volta)
Finale 2021–oggi in $ (SMA × EMA; uscita = EMA + 1):

| SMA \ EMA | 15 | 18 | 20 | 23 | 26 |
|---|---|---|---|---|---|
| 30 | 53.565 | 55.931 | 75.980 | 91.445 | 94.063 |
| 35 | 60.023 | 62.674 | 85.141 | 91.381 | 93.997 |
| **40** | 83.631 | 87.325 | **118.628** | 128.593 | 110.457 |
| 45 | 56.587 | 59.087 | 80.267 | 87.010 | 80.701 |
| 50 | 73.102 | 76.331 | 103.170 | 111.836 | 103.727 |

- Mediana dei vicini 100.671 $ (MAR 39,9), minimo 53.565 $, DD mediano −22,7%, peggiore −36,8%. Tutti battono il B&H.
- La base è all'80° percentile: bordo alto di un altopiano, con cresta sulla riga SMA 40 (SMA 35 e 45 perdono 30–40k).
  EMA sotto 20 porta il DD a −30/−35%.
- Trailing: 2,0 → 69.018 $ (DD −36,8%); 2,5 → 118.628; 3,0 → 109.119; 3,5 → 105.767.
- MACD × età: 8/21/5, 10/24/7, 12/26/9 quasi uguali (117–119k), 6/19/4 100.671; l'età 12–20 non cambia nulla nel 2021–26.
- Soglia flusso: −0,5 → 112.886; −0,25 → 86.717; 0 → 118.628; +0,25 → 100.416; +0,5 → 58.088 (non monotona: rumore da pochi trade).
- Moduli: senza F1 69.285 $ (DD −42,6%); senza flusso 75.337 $ (−34,4%); senza entrambi 41.064 $ (−49,3%).
- Nel 2018–20 la base è al 50° percentile (MAR 2,44, mediana 2,42) e la correlazione dei ranghi fra i due periodi è **−0,58**:
  i parametri migliori nel 2021–26 erano i peggiori nel 2018–20 (lì vinceva SMA 30, MAR 7).

## 5 · Walk-forward
54 configurazioni (SMA 30/40/50 × EMA 15/20/26 × trailing 2/2,5/3 × F1 sì/no), scelta per MAR sulla finestra 2018 → anno prima
(dal 2018 e non dal 08/2017 come scritto in PREREG: il proxy di flusso parte a fine 11/2017).

| | Finale | CAGR | DD | MAR |
|---|---|---|---|---|
| Walk-forward cucito | 59.946 $ | 35,8% | −38,7% | 12,9 |
| Config fissa (stessa simulazione continua) | 133.734 $ | 55,7% | −22,7% | 54,6 |
| Mediana delle 54 | 73.420 $ | | −36,8% | |

La config fissa è **1ª su 54** nel 2021–26 ma era 13ª–29ª nelle finestre di scelta: nessuno l'avrebbe scelta in anticipo.
Il walk-forward sceglie sempre SMA 30. Con F1 la mediana è 88.140 $, senza 60.957 $: F1 aiuta in tutta la griglia.

## 6 · Attese oneste a 3 anni (block bootstrap, 156 settimane)
| Scenario | CAGR 10° / 50° / 90° | DD mediano / 10° / 1° | P(3 anni in perdita) | P(DD oltre −40%) |
|---|---|---|---|---|
| A 2021–26 in campione (ottimista) | 14% / 47% / 97% | −24 / −37 / −49 | 2% | 6% |
| B 2018–26 in uso, flusso proxy | 14% / 52% / 119% | −24 / −40 / −56 | 3% | 10% |
| **C = B con haircut 35%** | **−3% / 31% / 88%** | **−31 / −50 / −66** | **12%** | **26%** |
| D 2018–26 senza F1 | −6% / 37% / 105% | −37 / −64 / −82 | 15% | 42% |

Tutti gli scenari ricampionano anni in cui BTC è salito di 2,6 volte: se BTC sale meno, anche la regola rende meno.
Ultimi due anni reali della regola: 2025 +1,9%, 2026 +10,2%.

Casi peggiori (rendimento / DD):

| Caso | In uso | Senza F1 | MACD 12/26/9 | Senza flusso | B&H |
|---|---|---|---|---|---|
| 2018 dal top (17/12/2017) | −35 / −50 | −65 / −73 | −54 / −65 | −36 / −50 | −80 / −83 |
| 2022 (dal 08/11/2021) | +19 / −13 | +19 / −13 | +19 / −13 | −9 / −31 | −76 / −77 |

Stop iniziale di un long oggi: 20,7% del prezzo (mediana 2021–26 25,8%, massimo 68,7%).

## Fatto esterno (audit del codice, non verificato qui)
Dal vivo la decisione usa il flusso perp del sabato (quello della domenica non è ancora disponibile); il backtest usa la domenica.
Rifatto "come dal vivo": 13 trade, 10k → ~103k invece di ~118,6k. Conferma che il finale è sensibile a dettagli di un giorno:
il numero da comunicare è ~103k o meno, non 119k.

## Cosa dire all'utente
- Vantaggio reale: evitare i bear restando nei trend. Regge su vicini, bootstrap e 2018–20.
- Numeri di facciata gonfiati: 119k è il primo posto su 54; attesa ragionevole 60–100k sullo stesso periodo, WR 65–75%, DD −30/−40%.
- Prossimi 3 anni: centro +15/+35% l'anno, intervallo −5% … +90%; DD atteso −30/−35%, uno su quattro oltre −40%.
- Caso peggiore realistico: top come il 2018 = −35/−40% (un solo long), DD −50%; fino a −65/−73% se il MACD non filtra.

## Lezione proposta per RESEARCH.md (83)
**Lezione 83**: W2 + MACD batte il buy & hold in modo robusto (90% dei ricampionamenti, 50 vicini su 50, 2018–20), ma i numeri
di facciata sono il massimo di una famiglia: la config in uso è 1ª su 54 nel 2021–26 e a metà classifica prima, il walk-forward
dà 60k con DD −39%, senza F1 69k con WR 68%. Attesa onesta: +15/+35% l'anno, DD −30/−40%. Un top come gennaio 2018 costa
−41% in un solo long (stop iniziale 2,5 ATRw senza tetto di rischio; F1 ferma solo i rientri) e la protezione dipende dal MACD
8/21/5 (con 12/26/9: −52%). Idea aperta n. 1 da riformulare: tetto di rischio sui long quando lo stop iniziale supera ~25%.

File: `lib.py`, `s2_storia.py`, `s3_trade.py`, `s4_vicini.py` (anche punto 1), `s5_walkforward.py`, `s6_attese.py`; CSV `s1`…`s6`.
