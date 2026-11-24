# Opzioni su BTC: struttura, uscite e segnali · ciclo notturno 24–25/11/2026 (PREREG + ADDENDUM-1 + ADDENDUM-2)

**Verdetto: niente batte la regola in uso. Il segnale per operare in opzioni su BTC resta quello di W3.2 con le 7 regole
(B0r).** Nessuna struttura (F1), nessuna uscita (F2) e nessun segnale indipendente (F3) supera i criteri preregistrati contro B0r.
Nessun segnale F3 è "utile" come fonte di occasioni in più: placebo p fra 0,22 e 0,31 e, senza le 2 operazioni migliori, sotto
10.000 $.

Con 10.000 $ e il 5% del conto per operazione, B0r vale una **forchetta**, non un numero esatto:

| | Prezzi veri degli scambi Deribit | Superficie |
|---|---|---|
| Dal 2018, solo operazioni chiuse | 45.000 $ | 48.258 $ |
| Dal 2018, con l'operazione aperta valutata al 21/11 (guadagno non realizzato) | ≈ 47.900 $ | 50.875 $ (DD −12,8%) |
| Dal 2021, solo operazioni chiuse | 27.343 $ | 28.320 $ |
| Dal 2021, con l'operazione aperta | ≈ 29.100 $ | 29.856 $ (DD −9,8%) |

B0r rende circa quanto W3.2 a metà dimensione (57.961 $ / 31.218 $) e non perde mai più del 5% per operazione. Il primo ciclo
riportava 49.712 $ dal 2018: quel numero usava il venerdì più vicino a 30 giorni senza la finestra 20–50 giorni della regola 3
(`radar/opzioni.py`, GG_MIN/GG_MAX), con 6 operazioni su 23 a 11–18 giorni. Era un errore di specifica, corretto con l'ADDENDUM-2.

## Cosa è stato provato
- **B0r** (regola in uso): segnale di W3.2, call se long e put se short, ingresso lunedì 12:00 UTC. Scadenza: il venerdì
  scambiato più vicino a 30 giorni **fra 20 e 50 giorni**; se non ce n'è, l'operazione si salta (2018-01-08 e 2018-10-15). Prezzo
  d'esercizio più vicino sulla griglia reale, 5% del conto, vendita all'uscita di W3.2, mai rinnovi.
- **F1**: scadenza ≈14/30/60/90 giorni (finestre 10–20, 20–50, 45–80, 70–120) × prezzo d'esercizio 5% dentro, alla pari, 5% e 10%
  fuori (16 celle).
- **F2**: uscite U0–U5.
- **F3**: segnali a–f con le soglie dell'ADDENDUM-1, più "call sempre" e "straddle sempre" come riferimenti.
- **F4 e spread a debito**: descrittivi.
- **Regole comuni**: ogni periodo è simulato da solo partendo da 10.000 $; costi del PREREG (3% del premio per lato, commissione
  0,03% con tetto 12,5%, esercizio 0,02%); valutazione giornaliera al valore di liquidazione.
- **Prezzi**: superficie di volatilità implicita Deribit 2018–26 (`superficie.py`), F = prezzo Binance delle 12:00.

Esecuzione:

| Script | Cosa fa | File prodotti |
|---|---|---|
| `op_fase2.py` (≈ 15 min) | cancello, famiglie e criteri | `risultati.txt`, `griglia_F1.csv`, `uscite_F2.csv`, `segnali_F3.csv`, `verdetti.csv`, `placebo.csv`, `equity.csv`, `operazioni_*.csv` |
| `op_veri.py` | B0r con gli scambi veri | `b0r_prezzi_veri.csv` |
| `op_d.py` | descrittivi per chi opera a mano | `descrittivi_D.txt` |

I risultati del primo ciclo (senza finestra) sono in `ciclo1/`. Il motore ha i test in `op_test.py` (9 test, verdi).

## Cancello (rafforzato, ADDENDUM-2 C)
- **Stesso contratto del CSV, prezzi della superficie**: scarto mediano del moltiplicatore +4,9% (soglia ±15%), superato.
- **Conto composto (5% per operazione, n. 1–22)**: con i moltiplicatori veri del CSV 49.101 $, con il motore sugli stessi
  contratti 56.390 $ (+15%). Circa 9 punti di questa differenza vengono dalla sola n. 3 del 2018: senza di essa, 43.125 contro
  45.573 $. L'incertezza dei prezzi sul conto composto è quindi di circa ±15%.
- **B0r con prezzi veri** (scambio vero del contratto più vicino all'istante, entro ±6 ore: 21 ingressi su 21 e 7 uscite su 7;
  scarto mediano 0,4 ore all'ingresso, massimo 3,3 ore; si usa l'ultimo scambio, a prescindere dal lato denaro o lettera):

| Periodo | Prezzi veri | Superficie | Differenza |
|---|---|---|---|
| Dal 2018 | 45.000 $ | 48.258 $ | −6,8% |
| Dal 2021 | 27.343 $ | 28.320 $ | −3,4% |
| IS 2018–21 | 22.771 $ | 24.454 $ | −6,9% |
| OOS 2022–26 | 19.762 $ | 19.734 $ | +0,1% |

Operazioni chiuse, conto composto. Tutte le differenze sono dentro l'incertezza di ±15%.

## Risultati (10.000 $; finale e DD giornaliero; superficie)
| Strategia | Dal 2018 | DD | Dal 2021 | DD | IS 2018–21 | DD | OOS 2022–26 | DD | Op. IS/OOS | PF OOS |
|---|---|---|---|---|---|---|---|---|---|---|
| W3.2 intera | 241.439 | −37,3 | 84.330 | −21,1 | 54.910 | −37,3 | 43.970 | −21,1 | 12/10 | 40,3 |
| W3.2 a metà | 57.961 | −22,6 | 31.218 | −11,9 | 26.404 | −22,6 | 21.951 | −11,9 | 12/10 | 40,3 |
| Buy & hold | 43.903 | −81,2 | 20.819 | −76,6 | 33.696 | −81,2 | 13.029 | −66,9 | — | — |
| **B0r (regola in uso)** | **50.875** | −12,8 | **29.856** | −9,8 | **24.454** | −12,8 | **20.805** | −9,8 | 10/10 | 11,1 |
| F1 scelta su IS: 30 g 5% fuori | 66.347 | −15,0 | 33.608 | −12,7 | 28.784 | −15,0 | 23.050 | −12,7 | 10/10 | 7,0 |
| F2 scelta su IS: U0 (= B0r) | = B0r | | | | | | | | | |
| F2 U5 un rinnovo | 47.168 | −14,4 | 29.137 | −12,8 | 22.364 | −14,4 | 21.091 | −12,8 | 13/17 | 3,6 |
| F3a tendenza | 20.441 | −34,9 | 13.607 | −32,4 | 13.537 | −34,9 | 15.583 | −28,0 | 46/55 | 1,39 |
| F3b flusso W3.2 ogni settimana (descr.) | 50.005 | −19,1 | 24.565 | −19,1 | 26.554 | −19,1 | 18.831 | −19,1 | 15/23 | 2,34 |
| F3c volatilità bassa → straddle | 12.756 | −28,5 | 10.282 | −28,5 | 12.003 | −14,1 | 10.662 | −28,5 | 22/41 | 1,15 |
| F3d compressione → straddle (descr.) | 15.650 | −13,8 | 15.285 | −6,6 | 10.451 | −13,8 | 14.975 | −6,6 | 13/15 | 5,07 |
| F3e dopo cascata → call (descr.) | 10.730 | −26,3 | 9.724 | −26,3 | 12.691 | −20,1 | 8.455 | −26,3 | 11/5 | 0,17 |
| F3f cono ≥ 1,4 × costo | 36.507 | −39,8 | 12.614 | −38,5 | 29.287 | −28,2 | 12.466 | −38,5 | 36/45 | 1,39 |
| Rif. call sempre | 44.447 | −43,9 | 18.471 | −43,9 | 23.811 | −31,1 | 18.667 | −35,9 | 47/58 | 1,65 |
| Rif. straddle sempre | 16.500 | −23,5 | 12.971 | −23,5 | 11.697 | −15,6 | 14.106 | −23,5 | 47/58 | 1,38 |
| F4 W3.2 metà su perp + protezione (descr.) | 29.231 | −33,2 | 21.244 | −13,4 | 17.315 | −33,2 | 16.882 | −13,4 | 12/10 | 9,1 |
| Spread a debito alla pari − 20% (descr.) | 31.514 | −9,2 | 24.773 | −9,2 | 16.593 | −8,4 | 18.992 | −9,2 | 10/10 | 10,6 |

Le griglie complete, con CAGR, quota in guadagno, perdita peggiore, serie peggiore e risultato senza le 2 migliori, sono in
`risultati.txt` e nei CSV. Riconteggio con la IV della superficie: c 25/37 operazioni (giudicabile), f 36/45.

## Criteri, uno per uno (OOS 2022–26 contro B0r: 20.805 $, DD −9,8%, 13.068 $ senza le 2 migliori)
| Cella | (1) finale > B0r e DD ≤ +3 punti | (2) senza le 2 migliori | (3) vicini | (4) ≥ 20 per metà e placebo | (5) Holm | Esito |
|---|---|---|---|---|---|---|
| F1 30 g 5% fuori | sì (23.050; −12,7%) | no (12.205) | 2/4 | — | p 0,27 → 1,00 | non migliore |
| F2 U0 | scelta IS = B0r | | | | | nessun cambio |
| F3a | no (15.583; −28,0%) | no (9.698) | 0/4 | 46/55, p 0,28 | 1,00 | non migliore, non utile (correlazione con B0r 0,50) |
| F3c | no (10.662; −28,5%) | no (8.348) | 0/4 | 22/41, p 0,22 | 1,00 | non migliore, non utile (PF 1,15) |
| F3f | no (12.466; −38,5%) | no (6.577) | 0/4 | 36/45, p 0,31 | 1,00 | non migliore, non utile; non batte "call sempre" (18.667) |

**Contro B0r i verdetti non cambiano rispetto al primo ciclo.** Cambia solo la cella scelta in F1: era "14 g alla pari", ora è
"30 g 5% fuori". Questa cella fa più di B0r in OOS, ma perché è più leva: senza le 2 migliori operazioni scende sotto B0r e solo 2
vicini su 4 restano sopra.

**U5 (un rinnovo)** nel primo ciclo, contro il vecchio B0: OOS 23.922 $, DD −12,8% contro −9,8%.
- Supera il punto 2: 14.532 $ contro 13.656 $ senza le 2 migliori.
- Non supera il punto 1, per 0,02 punti di DD.
- Non supera i vicini.
- Viola la regola 7 ("mai rinnovare").
- È soprattutto più esposizione: 36 operazioni contro 22 dal 2018.

Con B0r non è scelta su IS (22.364 contro 24.454 $) e in OOS, senza le 2 migliori, scende sotto B0r (12.787 contro 13.068 $).

## Cosa dicono i dati
- **Il guadagno viene dai segnali di W3.2, non dall'opzione.** Le 3 operazioni migliori di B0r (02/2024, 10/2020, 12/2020: +25–26%
  sul conto) sono le stesse di W3.2. Per lato: call +290% su 15 operazioni, put +24% su 5. B0r è positivo in tutti e tre i terzili
  di volatilità implicita all'ingresso.
- **Più occasioni non vuol dire più vantaggio.** a ed f stanno in posizione l'80–90% del tempo: sono "una call ogni mese" con
  DD del 30–40% (f contro call sempre in OOS: 12.466 contro 18.667 $). Le date a caso fanno quasi altrettanto (placebo p
  0,22–0,31).
- **Le scadenze sotto i 20 giorni sono escluse dalla regola in uso**, e i dati spiegano perché. Con il venerdì più vicino senza
  limiti, nel 2018–20 la scadenza cadeva a 11–18 giorni e il risultato della singola operazione diventava molto più casuale (ciclo 1).
- **Prese di profitto a 2× o 3×, vendita 7 giorni prima e rinnovo peggiorano o non migliorano B0r.** OOS 14.779 / 16.616 / 17.634 /
  19.175 / 21.091 $ contro 20.805 $. Le prese di profitto tagliano proprio le operazioni che fanno il risultato.
- **L'opzione al posto dello stop (F4) costa più di quanto protegga**: 29.231 $ dal 2018 con DD −33% contro W3.2 a metà 57.961 $ e −22,6%.
  **Lo spread a debito** taglia i movimenti grandi: 31.514 $ dal 2018 e 18.992 $ in OOS.
- **Costi**: con differenza denaro-lettera 0/3/6% per lato B0r fa 56.650 / 50.875 / 45.923 $ dal 2018. L'ordine fra le strategie
  non cambia.
- **Unica eccezione da tenere d'occhio: F3d (compressione delle bande → straddle).** In OOS 14.975 $, DD −6,6%, PF 5,1, ma con
  13/15 operazioni resta descrittivo (meno di 20 per metà).

## Per chi opera a mano (ADDENDUM-2 D, descrittivi su B0r, operazioni chiuse)
**Ritardo d'ingresso e soglia del 3%** (conto composto da 10.000 $; soglia = si entra solo se BTC è entro ±3% dalla chiusura
della domenica):

| Ingresso | Dal 2018 | Dal 2021 | OOS | Con la soglia del 3%: operazioni | Dal 2018 | OOS |
|---|---|---|---|---|---|---|
| Lunedì 00:00 | 49.785 | 29.139 | 20.217 | 20 di 20 | 49.785 | 20.217 |
| Lunedì 12:00 (B0r) | 48.258 | 28.320 | 19.734 | 15 di 20 | 38.406 | 20.773 |
| Martedì 00:00 | 41.063 | 25.829 | 17.871 | 15 di 20 | 30.859 | 14.372 |
| Mercoledì 00:00 | 37.500 | 25.610 | 18.494 | 12 di 20 | 18.290 | 16.354 |
| Giovedì 00:00 | 32.030 | 22.091 | 17.690 | 10 di 20 | 13.072 | 10.698 |

- **Il ritardo costa, ma non in modo uniforme.** Il primo giorno vale −17% sul conto, ma per l'85% è dovuto a 2 operazioni partite
  forte (2019-05 e 2023-10): senza di esse ≈ −3%. Da lunedì 00:00 a martedì 00:00 peggiorano 11 operazioni e migliorano 8. Oltre le
  48 ore il peggioramento è diffuso (15 operazioni su 19 peggiorano fra 48 e 72 ore).
- **La soglia del 3% non è giustificata.** Con ingresso a mezzogiorno del lunedì esclude 2 vincenti grandi e 3 perdenti: il saldo
  (−20%) dipende da 2 operazioni e in OOS la soglia fa meglio (20.773 contro 19.734 $). Con ingressi a 24 ore o più tardi esclude
  soprattutto vincenti (6 su 8 a 48 ore, 10 su 10 a 72) e peggiora nettamente.
- **Ricampionamento con ipotesi più severe** (verifica finale; 1.500 $ fissi, 3 anni):

| Ipotesi | Probabilità di perdita | Risultato mediano | 5° percentile |
|---|---|---|---|
| Storico | 0,9% | +18.100 $ | +4.900 $ |
| Solo moltiplicatori OOS | 1,1% | +15.200 $ | +3.700 $ |
| Senza le 3 operazioni migliori | 3,0% | +11.700 $ | +1.300 $ |
| Senza le 3 migliori e numero di operazioni casuale | 5,0% | +10.600 $ | 0 $ |
| Operazioni in guadagno al 50% | 11,4% | +9.300 $ | −3.000 $ |
| Al 50% e senza le 3 migliori | 17,4% | +5.900 $ | −3.800 $ |

**Cosa aspettarsi su 3 anni** (circa 7 operazioni; 10.000 estrazioni con reinserimento dei 20 moltiplicatori di B0r):

| Quota per operazione | Percentili 5 / 25 / 50 / 75 / 95 | Probabilità di perdita | Serie peggiore di premi persi |
|---|---|---|---|
| 5% del conto (da 10.000 $) | 11.473 / 14.519 / 17.353 / 20.700 / 26.834 $ | 1,2% | mediana 1 operazione (−5%), 5° percentile −9,8% |
| 1.500 $ fissi | +4.784 / +12.367 / +18.182 / +24.038 / +32.710 $ | 1,1% | mediana −1.500 $, 5° percentile −3.000 $ |
| 2.000 $ fissi | +6.379 / +16.489 / +24.243 / +32.050 / +43.613 $ | 1,1% | mediana −2.000 $, 5° percentile −4.000 $ |

Nello storico, con 1.500 $ fissi per operazione si sarebbero guadagnati +52.136 $ dal 2018; con 2.000 $, +69.515 $. Questi numeri
presuppongono che i segnali di W3.2 restino buoni come nel 2018–26: il 25% delle operazioni in perdita, il 10% con il premio perso
del tutto.

## Cosa significa per l'operatività
Per chi vuole segnali per operare in opzioni su BTC:
- **Quale segnale usare**: solo il segnale di W3.2, con le 7 regole. Call se long, put se short. Il venerdì più vicino a 30
  giorni fra quelli a 20–50 giorni, prezzo d'esercizio più vicino al prezzo, 5% del conto o una cifra fissa. Si vende quando
  W3.2 esce, mai rinnovare.
- **Cosa aspettarsi**: circa 2–3 operazioni l'anno. Su 10.000 $ dal 2018 fra 45.000 e 48.000 $ sulle operazioni chiuse, dal 2021
  fra 27.000 e 28.000 $, con DD intorno al −10/−13% e perdita massima del 5% per operazione. Con 1.500 $ a operazione il risultato
  tipico su 3 anni è intorno a +18.000 $ (+24.000 $ con 2.000 $) **se i segnali restano come nel 2018–26**: in quel caso la
  probabilità di chiudere 3 anni in perdita è dell'1–5% (5% togliendo le 3 operazioni migliori). Se le operazioni in guadagno
  scendessero al 50%, salirebbe al 12–19%, con un risultato tipico di +6.000 / +9.000 $ a 1.500 $ per operazione.
- **Cosa evitare**:
  - opzioni fra un segnale e l'altro (a, c, e, f e "call sempre": esposizione senza vantaggio dimostrato);
  - scadenze sotto 20 giorni;
  - prese di profitto a 2× o 3×;
  - rinnovi;
  - l'opzione al posto dello stop.
- **Quando entrare**: il lunedì, senza rimandare. La differenza fra 00:00 e 12:00 è dentro il rumore (9 operazioni peggiorano, 10
  migliorano); il costo vero arriva con 1–3 giorni di ritardo. La soglia del 3% non è giustificata: non migliora in modo stabile e
  con ingressi tardivi toglie i segnali migliori.
- **Solo in osservazione**: F3d (compressione → straddle) sulla carta, se l'utente lo approva; non si opera.

## Limiti
- **Tempi**: ingresso alle 12:00 UTC del lunedì, circa 12 ore dopo il segnale. Le uscite di W3.2 durante la giornata si vendono il
  giorno dopo.
- **Superficie**: quella del giorno include scambi dopo le 12:00 (lieve anticipo).
- **Regolamento**: apertura oraria Binance delle 08:00, non l'indice Deribit.
- **Prezzi**: incertezza di circa ±15% sul conto composto. F è il prezzo spot, non il future.
- **Placebo sbilanciato a favore del segnale**: con molte operazioni le date a caso a volte si saltano, quindi il placebo ha
  meno esposizione (per questo "call sempre" ha p 0,03 contro le sue stesse date a caso). Il verdetto negativo su F3 ne esce
  rafforzato.
- **Campione piccolo**: 20 operazioni chiuse per B0r, 10 in OOS. Flusso perp vero solo dal 2020-04, funding dal 2020-01, dati
  fino al 2026-11-21.
- **Prezzi veri**: sono gli ultimi scambi del contratto, anche da 0,1 BTC e talvolta al prezzo denaro (es. ingresso del 2022-08):
  il costo d'ingresso può essere sottostimato.
- **Descrittivi sul ritardo**: l'ingresso alle 00:00 usa la superficie dell'intera giornata, che contiene prezzi successivi.
- **Operazioni saltate nel 2018** (nessun venerdì quotato fra 20 e 50 giorni): 2018-01-08 era una perdita di W3.2 (−25%);
  2018-10-15 era uno short di W3.2 in guadagno (+16,7%) e la put sarebbe stata probabilmente redditizia. Nel complesso il salto
  non gonfia B0r.

## Deviazioni dal PREREG (dichiarate)
- **Holm per F1 e F2**: test appaiato a segni casuali sulle operazioni contro il riferimento, moltiplicato per 15 e per 5. Per F3
  si usa il p del placebo × 6.
- **Scelta su IS**: il finale IS più alto fra le celle con DD non peggiore del riferimento di oltre 3 punti.
- **Vicini**: F1 sono le celle adiacenti della griglia. F2 sono i parametri ±: 1,5/2,5×, 2,5/3,5×, 5/10 giorni; per U5, 21/45
  giorni. F3 sono le soglie adiacenti e le scadenze 21/45 giorni (finestra 20–50).
- **"Utile", punto 2**: interpretato come "sopra 10.000 $ senza le 2 migliori".
- **Secondo ciclo**: ammesso dal PREREG per l'errore di specifica del riferimento. Tutto è esplorativo, come scritto
  nell'ADDENDUM-2.

## Secondo ciclo (ADDENDUM-2): cosa è stato fatto
- A. B0r con la finestra 20–50 giorni della regola in uso, diventato il riferimento; 2 operazioni del 2018 saltate.
- B. F1, F2 e F3 rieseguiti con finestre coerenti e giudicati contro B0r: nessun verdetto cambia.
- C. Cancello sul conto composto e B0r con gli scambi veri di Deribit.
- D. Descrittivi per chi opera a mano.

**Non è stato eseguito il filtro sulla volatilità implicita alta** proposto dalla diagnosi del primo ciclo. I terzili erano
calcolati sugli stessi dati 2018–26, OOS compreso: sarebbe stata una pesca a posteriori. Inoltre B0r è positivo in tutti i
terzili, quindi il filtro non tocca la regola in uso.

## Lezione proposta per RESEARCH.md
"N. (opzioni, 25/11/2026) Comprare opzioni su BTC non crea un vantaggio proprio. La regola in uso (B0r: segnale di W3.2, venerdì più vicino a 30
giorni fra 20 e 50, alla pari, 5%) vale 45–48k $ dal 2018 su 10k sulle operazioni chiuse (prezzi veri e superficie), circa come W3.2 a
metà, con perdita massima del 5%. Struttura, uscite, rinnovi e segnali indipendenti non la battono in OOS: le occasioni in più sono
esposizione alla salita di BTC (placebo p ≥ 0,22). Prima di confrontare, simulare la regola esattamente come è scritta nel tool:
senza la finestra 20–50 giorni il riferimento era sbagliato. Dare il risultato come forchetta a parità di operazioni: i prezzi
ricostruiti spostano il conto composto fino al 15%. I descrittivi per chi opera a mano dipendono da 2–3 operazioni: vanno riportati
con il conteggio di quante operazioni migliorano e quante peggiorano."
