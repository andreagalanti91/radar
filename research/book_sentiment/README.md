# Indicatore di sentiment da order book e liquidazioni · 22/11/2026 · L non è un segnale; I e S non dimostrati

**Verdetto.** Il segno di S (e di I e L da soli) non predice il rendimento di BTC a 1, 4 o 24 ore in nessuno dei 14 test
preregistrati (nessun p grezzo sotto 0,05, tutti i p di Holm = 1,00). La regola "long se S > +0,2, short se S < −0,2" perde dopo
i costi: 10.000 $ → 6.907 $ in 16 giorni (buy & hold 7.968 $), e sulle sole liquidazioni reali 2023–24 azzera il capitale
(3.893 operazioni, lordo −4,5%). Distinzione di potenza:
- **1 ora**: test adeguato per un effetto utile (≥ 0,40%): **nessun effetto utile**. Un effetto piccolo (0,10%) non è escluso sul
  registro del book; è invece escluso per le liquidazioni da sole (16 mesi, Δ +0,001%, IC ±0,02%).
- **4 e 24 ore sul registro del book (16 giorni)**: **non dimostrabile con questi dati** (effetto minimo rilevabile 0,5% e 1,0%).
- L "ripete" la mossa appena avvenuta (correlazione +0,53/+0,57 con il rendimento dell'ora precedente) e S è in pratica L
  (stesso segno in 253 foto su 275): l'indicatore descrive ciò che è successo, non ciò che succederà.

Preregistrazione: PREREG.md, commit `dacb01d` (da solo, prima di ogni rendimento). Script: bs_data.py, bs_conteggi.py, bs_run.py.
Output: conteggi.txt (prima del PREREG), risultati.txt, q1_celle.csv, q2_regola.csv, muri_coppie.csv.

## Inventario dei dati
| Fonte | Contenuto | Frequenza | Intervallo | Uso |
|---|---|---|---|---|
| data/orderbook.csv | profondità bid/ask e squilibrio a ±0,25/0,5/1/2% (5 borse aggregate), 1 muro per lato, spread | ~8/giorno, oraria dal 14/11 | 07/11 → 22/11/2026, 275 foto | I (±1% esatto) · insieme A |
| data/liq_events/2026-11.csv | eventi reali (ms): OKX 47.515, Gate 23.149, dYdX 1.075, Deribit 31, Kraken 7, Lighter 8 | evento | 10–11/11 → 22/11 | L a 30 minuti · A |
| data/liquidations.csv | OKX, ultimi 100 eventi per giro (incompleto nelle cascate) | evento | 30/10 → 22/11 | L prima del 10/11 · A |
| data.binance.vision COIN-M BTCUSD_PERP | liquidazioni reali, 53.398 eventi, ~950 M$ | evento | 25/06/2023 → 14/10/2024 (472 giorni) | L oraria · insieme B |
| data/book_walls.csv | 3 muri per lato e per borsa | oraria | 1 sola foto (22/11 13:02) | nessuno (0 coppie) |
| data/liqsnap (Hyperliquid, Lighter) | livelli di liquidazione, non eventi | ~oraria | dal 11/11 | non pertinente a L |
| data/taker_1h.csv, spot_1h.csv | flusso taker e candele orarie | oraria | dal 2022 | prezzi di B |
| candele 1m BTCUSDT spot Binance | prezzi | 1 minuto | dal 06/11/2026 | prezzi di A |

Mancano: book prima del 07/11/2026; liquidazioni Binance USDT-M, Bybit, Hyperliquid (il registro vede meno del 10% del mercato);
ETH e altri asset; quindi niente tabella dal 01/01/2021 e niente "stessi parametri su tutti gli asset".

## Domanda 1 · il segno predice? Δ = rendimento medio dopo segno + meno dopo segno − (punti %)
| Test | N (+ / −) | Δ | IC 95% | p | p Holm | metà 1 / metà 2 | MDE 80% | Esito |
|---|---|---|---|---|---|---|---|---|
| A · S → 1h | 275 (127/148) | −0,117 | −0,30 / +0,04 | 0,20 | 1,00 | −0,18 / −0,09 | 0,24 | nessun effetto utile |
| A · S → 4h | 271 (125/146) | +0,014 | −0,35 / +0,45 | 0,96 | 1,00 | −0,13 / +0,07 | 0,52 | non dimostrabile |
| A · S → 24h | 250 (114/136) | −0,140 | −0,40 / +0,15 | 0,77 | 1,00 | −0,12 / −0,17 | 1,02 | non dimostrabile |
| A · I → 1h (non cieco) | 275 (172/103) | +0,057 | −0,04 / +0,16 | 0,55 | 1,00 | +0,03 / +0,06 | 0,25 | nessun effetto utile |
| A · I → 4h (non cieco) | 271 (170/101) | +0,204 | −0,24 / +0,63 | 0,38 | 1,00 | +0,08 / +0,24 | 0,63 | non dimostrabile |
| A · I → 24h (non cieco) | 250 (156/94) | +0,342 | −0,27 / +1,04 | 0,49 | 1,00 | +0,50 / +0,20 | 1,40 | non dimostrabile |
| A · L → 1h | 257 (115/142) | −0,118 | −0,32 / +0,04 | 0,20 | 1,00 | −0,22 / −0,08 | 0,26 | nessun effetto utile |
| A · L → 4h | 253 (113/140) | +0,091 | −0,30 / +0,53 | 0,65 | 1,00 | −0,16 / +0,17 | 0,55 | non dimostrabile |
| A · L → 24h | 232 (102/130) | −0,237 | −0,58 / +0,15 | 0,61 | 1,00 | −0,46 / −0,17 | 1,14 | non dimostrabile |
| B · L → 1h | 7.062 (3.005/4.057) | +0,001 | −0,02 / +0,02 | 0,92 | 1,00 | −0,02 / +0,02 | 0,03 | nessun effetto, nemmeno piccolo |
| B · L → 4h | 7.062 | −0,018 | −0,06 / +0,02 | 0,49 | 1,00 | −0,06 / +0,02 | 0,07 | nessun effetto, nemmeno piccolo |
| B · L → 24h | 7.062 | −0,020 | −0,16 / +0,11 | 0,77 | 1,00 | −0,06 / +0,02 | 0,19 | nessun effetto utile |

A = registro del book (07–22/11/2026, metà 07–14/11 e 15–22/11); B = liquidazioni reali Binance COIN-M (metà divise al 19/02/2024).
p da spostamento circolare a blocchi (5.000 / 2.000 ripetizioni), IC da bootstrap per giorni (A) e settimane (B).
A 1 ora S e L hanno segno NEGATIVO (dopo "pressione al rialzo" il prezzo ha reso meno), non significativo.

Controlli non di conferma: etichette a ±0,2 uguali al segno (A 1h −0,10%, B 1h +0,003%); L solo con ≥ 100.000 $: A 1h −0,18%
(n 157), B +0,006% (n 1.708); il "segnale" banale segno del rendimento dell'ora precedente dà lo stesso (A 1h −0,11%, B −0,02%);
segno(L) al netto del rendimento precedente: Δ ≈ −0,05% (A) e +0,02% (B) a 1 ora. Legame con il passato (Spearman con il
rendimento dell'ora precedente): L +0,53 (A) e +0,57 (B), I −0,51, S +0,47. I e L si contraddicono (correlazione −0,42): dopo una
salita il book è più pieno sugli ask e le liquidazioni sono di short.

## Domanda 2 · la regola dopo i costi (10.000 $ a 1x; 0,10% per lato = commissione 0,05% + slippage 0,05%)
| Insieme · variante | Finale | Rend. | Max DD giorn. | Trade | WR | MAR | Lordo | Senza trade migliore | Metà 1 / metà 2 |
|---|---|---|---|---|---|---|---|---|---|
| **A · V1 regola S ±0,2** | **6.907** | −30,9% | −30,9% | 139 | 29,5% | <0 | −8,8% | −33,6% | 8.636 / 8.088 |
| A · V2 / V3 soglia ±0,1 / ±0,3 | 6.868 / 7.095 | −31,3 / −29,0% | −31,3 / −29,0% | 139 / 136 | 29 / 30% | <0 | −9,3 / −6,9% | | tutte < 10.000 |
| A · V4 solo I | 9.386 | −6,1% | −8,3% | 18 | 50% | <0 | −2,7% | −7,1% | 9.545 / 9.833 |
| A · V5 solo L | 6.662 | −33,4% | −33,4% | 142 | 29% | <0 | −11,5% | | 8.482 / 7.943 |
| A · V6 L a 60 minuti | 7.510 | −24,9% | −25,1% | 116 | 26% | <0 | −5,3% | | 9.561 / 7.927 |
| A · V7 rovesciata | 8.169 | −18,3% | −20,5% | 139 | 53% | <0 | +7,9% | | 9.489 / 8.548 |
| A · V8 decisione ogni 4 ore | 8.304 | −17,0% | −20,2% | 35 | 29% | <0 | −10,9% | | 9.003 / 9.121 |
| A · buy & hold · W3.1 | 7.968 · ~10.290 | −20,3% · ~+2,9% | −21,9% | 1 · 1 | | | | | (W3.1: short dal 16/11, esposizione 0,389, aperto) |
| **B · V1 regola (S = 0,5·L)** | **4** | −100% | −100% | 3.893 | 22,9% | <0 | −4,5% | −100% | 178 / 223 |
| B · V2 / V3 / V7 | 3 / 4 / 4 | −100% | −100% | ~3.900 | 23–33% | <0 | −14,4 / −2,5 / −15,5% | | tutte < 400 |
| B · V8 decisione ogni 4 ore | 681 | −93,2% | −93,3% | 1.103 | 33% | <0 | −38,1% | | 2.268 / 3.007 |
| B · buy & hold · W3 | 21.614 · ~17.800 | +116% · ~+78% | −26,5% | 1 · 4 | | | | | (W3 approssimata dai trade storici) |

Placebo sul lordo: A p 0,79, B p 0,39 (Holm 1,00). Con costi di 0,075% per lato: A 7.404, B 28. Solo dal 11/11 (liquidazioni
multi-fonte): 7.261. Anche la regola rovesciata perde al netto: non c'è segnale e S cambia stato a quasi ogni foto (168 cambi in
275 foto), quindi i costi mangiano tutto. La tabella standard dal 01/01/2021 non è applicabile (i dati non esistono).

## Domanda 3 · dopo una cascata: già testato, non rifatto
research/liq_fasce (lezione 92): continuazione dopo cascata long, 345 eventi dal 2021, 10.000 → 3.074 $, p 0,78; sulle cascate
reali COIN-M (31 long) −0,53% per trade a 24 ore, 53 short con segni opposti fra le metà; rimbalzo su fascia + supporto (33 eventi)
p 0,50–0,68. research/liq_squeeze (lezione 93): tutte le regole perdono e non si distinguono dal caso. Nel registro attuale le
ore con ≥ 10 M$ e un lato ≥ 75% sono 17 long (9 episodi) e 4 short (3 episodi): non aggiungono potenza.

## Domanda 4 · muri ritirati: non testabile
data/book_walls.csv ha una sola foto (zero coppie). Con il muro unico di data/orderbook.csv e foto orarie, la definizione della
pagina (scomparsa ≥ 70% senza tocco del prezzo) produce **0 eventi su 454 muri osservati**; una definizione larga ne produce 46
(22 bid, 24 ask), che a un'ora di distanza sono normale ricambio di ordini. Descrittivo senza valore probatorio: dopo ritiro bid
+0,18% a 1 ora (n 22, dev. st. 1,15), dopo ritiro ask +0,16% (n 24). Per vedere una differenza di 0,40% (0,10%) fra i due lati
servono ~54 (~870) eventi per lato, registrati al secondo con la definizione della pagina (prezzo entro 0,3%, senza scambi).

## Cosa è testabile e cosa no
| Domanda | Stato |
|---|---|
| L da solo, 1–24 ore | testato con potenza adeguata (16 mesi): nessun effetto |
| S e I a 1 ora | testato per effetti ≥ 0,25%: nessuno; effetti di 0,10% non ancora verificabili |
| S e I a 4 e 24 ore | non dimostrabile: 16 giorni, un solo regime (76k → 61k) |
| Regola dopo i costi | perde; con S che cambia a ogni foto servirebbe Δ > 0,40% per pareggiare |
| Muri ritirati, ETH, book multi-borsa della pagina | nessun dato storico |

## Quando rifare il test (potenza 80%, α 0,05, foto orarie)
| Effetto cercato | 1 ora | 4 ore | 24 ore |
|---|---|---|---|
| 0,40% (utile) su S | già raggiunto | ~4 settimane | ~14 settimane |
| 0,10% (plausibile) su S | ~13 settimane (~1.600 foto: 10 se davvero orarie) | ~58 settimane | ~4 anni |
| con Holm su 14 test | × 1,8 | × 1,8 | × 1,8 |

Rifare a **metà febbraio 2027** (13 settimane dal 07/11) con un solo test primario preregistrato (S → 1 ora), usando l'S
calcolato come in pagina: il registro deve salvare a ogni foto I, L, S, i dollari liquidati per lato e per fonte. A 4 ore non
prima di dicembre 2027; a 24 ore il test non è realistico.

## Nota di disegno per la pagina (dai conteggi, nessuna ottimizzazione)
Con pesi 0,5/0,5 S è quasi solo L: L è bimodale (in 90 foto su 275 è liquidato un solo lato, quindi L = ±1) mentre I supera ±0,2
in 23 foto su 275. L'etichetta cambia quasi a ogni aggiornamento e, in metà dei casi, con meno di 190.000 $ di liquidazioni nella
finestra. Se la regia vuole un'etichetta stabile servono una soglia minima in dollari per L o i due componenti mostrati separati:
è una scelta di presentazione da preregistrare, non un miglioramento dimostrato.

## Frase da mostrare in pagina
> Indicatore descrittivo, non un segnale. Riassume lo squilibrio del book entro ±1% e le liquidazioni degli ultimi 30 minuti.
> Nei test (16 giorni di registro; 16 mesi di liquidazioni reali) il suo segno non ha anticipato il prezzo a 1, 4 o 24 ore e
> la regola long/short ha perso dopo i costi. Le liquidazioni seguono il movimento appena avvenuto. Prossima verifica: febbraio 2027.

## Deviazioni e limiti dichiarati
- L sul registro usa la finestra di 30 minuti (eventi al millisecondo) e non l'ora precedente indicata dalla regia come ripiego:
  è la specifica della pagina; l'ora precedente è usata in B e come variante V6. Scritto nel PREREG.
- "Nessun effetto utile" è stato letto contro l'effetto utile (0,40%); l'effetto plausibile (0,10%) è riportato a parte.
- Le celle su I non sono cieche (research/book_liq, stesso registro: ρ +0,14 a 1 ora; qui ρ +0,142, coerente).
- Prima del PREREG sono stati scaricati i prezzi a 1 minuto e usati solo per il tocco dei muri fra due foto (conteggi.txt).
- B è un mercato piccolo (COIN-M, evento mediano 1.700 $) e senza book: vale per L, non per S completo. In A le liquidazioni
  coprono meno del 10% del mercato e fino al 10/11 solo OKX.
- A: spostamento circolare per posizione con foto non equidistanti nella prima settimana; funding non incluso; prezzi spot Binance.
- Contesto W3.1/W3 approssimato (posizione aperta; trade storici di research/weekly_w3_trades.csv), non ricalcolato dal motore.

## Lezione proposta per RESEARCH.md
**Lezione 108**: un indicatore di sentiment S = 0,5·squilibrio del book (±1%) + 0,5·squilibrio delle liquidazioni (30 minuti)
non anticipa BTC: 0 test su 14 (Holm), regola long/short 10k → 6,9k in 16 giorni (buy & hold 8,0k) e capitale azzerato sulle
liquidazioni reali 2023–24 (3.893 operazioni, lordo −4,5%). Le liquidazioni ripetono la mossa dell'ora precedente (correlazione
+0,55) e dominano S; su 16 mesi il loro segno vale Δ +0,001% a 1 ora (IC ±0,02%): chiuso. Per book e S a 1 ora è escluso solo un
effetto ≥ 0,25%; a 4–24 ore 16 giorni non bastano ("non dimostrabile", non "non funziona"). Muri ritirati: 0 eventi con foto
orarie, serve un registro al secondo. In pagina l'indicatore va mostrato come descrizione, con la frase di avvertenza; rifare a
febbraio 2027 con un solo test primario (S → 1 ora). research/book_sentiment/README.md (PREREG dacb01d).

## Revisione critica (agente separato, 22/11/2026)
Il verdetto regge, con una riserva sulla formulazione: "non è un segnale" vale per L (16 mesi di liquidazioni reali). Per I e per
S a 4 e 24 ore l'esito corretto è "non dimostrabile": I ha correlazione di rango +0,14 a 1 ora con lo stesso segno nelle due metà,
quindi non è confutato, è non provato. Allineamento temporale e segni delle liquidazioni verificati alla lettura; `bs_run.py` non è
stato rieseguito dal revisore (cache dei prezzi assente). Nota: il backtest filtra gli eventi per orario dell'evento e non di
raccolta, quindi vede anche eventi recuperati dopo: favorisce l'indicatore e rafforza l'esito negativo. Dal 22/11 il registro lascia
L e S vuoti quando le liquidazioni dei 30 minuti sono sotto 250.000 $ (segno instabile: cambia entro 5 minuti nel 16% dei casi).
