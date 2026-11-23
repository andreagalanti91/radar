# Previsionale 2 · regimi di mercato e politica economica (BTC a 7 e 30 giorni, 23/11/2026) · NON FUNZIONA

**Verdetto (preregistrato: PREREG.md, commit 3a6a973, committato da solo prima di ogni risultato).**
Il 2021–26 era già stato guardato nel primo ciclo (lezione 112): criteri più severi (AUC ≥ 0,55 in entrambi i periodi, Brier
skill contro la base rate del regime, soglia relativa, Holm sui 16 test dei due cicli).

| Orizzonte | R · regimi + flusso/RSI/volatilità | P · politica economica | RP · entrambi |
|---|---|---|---|
| 7 giorni | **NON FUNZIONA** (AUC 0,51 / 0,52) | **NON FUNZIONA** (0,46 / 0,46: sotto il caso) | **NON FUNZIONA** (0,50 / 0,53) |
| 30 giorni | **NON FUNZIONA** (0,46 / 0,52) | **NON FUNZIONA** (0,40 / 0,56) | **NON FUNZIONA** (0,43 / 0,59) |

- Nessun modello arriva a AUC 0,55 nel 2021–23; P e RP a 30 giorni la superano solo nel 2024–26, dopo essere stati sotto il caso
  nel 2021–23: è il rovesciamento di segno già visto nel primo ciclo, non un'abilità. p dello sfasamento 0,28–0,88; Holm 1,00 su 16.
- **La politica economica non aggiunge nulla al flusso perp: lo peggiora.** Flusso da solo (PF) contro flusso + politica (PF+P):
  ΔAUC −0,047 a 7 giorni (IC 95% −0,086 / −0,007) e −0,071 a 30 giorni (−0,170 / +0,024).
- Il flusso perp da solo resta l'unica cosa con un po' di ordine (AUC 0,58 / 0,57 a 30 giorni, p 0,09), ma non batte "sale
  sempre" in entrambi i periodi ed è già dentro W3.2.
- **W3.2: 0/3 varianti.** W3.2 resta com'è.
- I regimi e le fasi della Fed DESCRIVONO bene cosa è successo (sezione "Studio"), ma con 1 episodio per fase e 4–10 per stato
  non permettono di prevedere. In dashboard: stato di regime e politica come **contesto**, senza probabilità.

Metodo: stessi dati BTC congelati del primo ciclo (taglio 15/11/2026) e stesso codice (fc_data, fc_models, fc_run importati);
logistiche L2 con λ scelto nell'addestramento, walk-forward espansivo dal 2015, riaddestramento mensile, embargo = orizzonte.
Regimi: T = prezzo contro SMA200 e sua pendenza a 30 giorni (U rialzo / M misto / D ribasso); V = volatilità a 30 giorni contro
la propria mediana dei 365 giorni precedenti (A alta / B bassa). Politica (8 variabili FRED con il ritardo reale di
pubblicazione): direzione del tasso a 6 mesi, liquidità netta a 13 settimane, variazione del rendimento reale, curva 10–2 anni,
dollaro a 3 mesi, VIX, FOMC entro 7 giorni, segno della variazione del CPI annuo. Soglia relativa: "su"/"giù" se la probabilità è
nel terzo alto/basso delle previsioni PASSATE nello stesso regime. Potenza: ~150 osservazioni indipendenti per periodo a 7 giorni,
~35 a 30 giorni: AUC minima dimostrabile ≈ 0,58–0,62 a 7 giorni e 0,67–0,75 a 30 giorni.

## Risultati fuori campione (AUC · Brier skill contro la base rate del regime · direzioni corrette con soglia relativa [copertura])
| h | Modello | 2021–23 | 2024–26 | AUC 2021–26 (IC 95% a blocchi) | p sfasamento | "sale sempre" sugli stessi giorni 21–23 / 24–26 |
|---|---|---|---|---|---|---|
| 7 | R | 0,51 · +0,5% · 48,3% [57%] | 0,52 · −0,5% · 52,2% [79%] | 0,52 (0,46–0,56) | 0,28 | 53,6% / 49,8% |
| 7 | P | 0,46 · −1,5% · 49,5% [68%] | 0,46 · −0,2% · 46,8% [44%] | 0,46 (0,41–0,51) | 0,88 | 50,5% / 53,2% |
| 7 | RP | 0,50 · −0,9% · 51,0% [61%] | 0,53 · +0,2% · 51,1% [75%] | 0,51 (0,46–0,55) | 0,37 | 53,1% / 52,0% |
| 7 | PF (solo flusso, ausiliario) | 0,52 · +0,5% · 52,1% [51%] | 0,53 · 0,0% · 54,1% [66%] | 0,53 (0,48–0,57) | 0,19 | 53,0% / 51,0% |
| 7 | PF+P (ausiliario) | 0,48 · −0,5% · 50,2% | 0,49 · 0,0% · 48,5% | 0,48 (0,43–0,53) | 0,79 | 49,8% / 53,6% |
| 7 | base rate del regime da sola | AUC 0,43 | AUC 0,50 | 0,46 | – | |
| 30 | R | 0,46 · +1,8% · 40,4% [55%] | 0,52 · +0,6% · 56,3% [69%] | 0,49 (0,40–0,58) | 0,57 | 54,9% / 51,5% |
| 30 | P | 0,40 · −1,0% · 48,7% [78%] | 0,56 · +2,7% · 53,2% [67%] | 0,47 (0,35–0,58) | 0,75 | 48,5% / 56,7% |
| 30 | RP | 0,43 · −0,3% · 47,3% [67%] | 0,59 · +1,3% · 57,1% [86%] | 0,50 (0,39–0,61) | 0,53 | 49,8% / 53,7% |
| 30 | PF (solo flusso, ausiliario) | 0,58 · +3,7% · 56,6% [78%] | 0,57 · +1,5% · 50,2% [78%] | 0,56 (0,49–0,64) | 0,09 | 48,9% / 54,5% |
| 30 | PF+P (ausiliario) | 0,41 · −4,5% · 49,9% | 0,62 · +3,9% · 58,6% | 0,49 (0,38–0,60) | 0,60 | 47,6% / 54,8% |
| 30 | base rate del regime da sola | AUC 0,38 | AUC 0,52 | 0,42 | – | |

Gli intervalli del Brier skill comprendono lo zero per tutti i modelli e periodi. Contro la persistenza e il lato di W3.2 sugli
stessi giorni (tabella2.csv): nessun modello è sopra tutti e tre i riferimenti in entrambi i periodi; l'accuratezza a blocchi non
sovrapposti coincide al decimo. Con la soglia relativa i modelli ora dicono anche "giù" (a 30 giorni RP: 359 "su" corretti al
60%, 1.248 "giù" corretti al 50,5%): tolto il limite di disegno del primo ciclo, l'esito non cambia.
Controllo di sanità (non preregistrato): un segnale finto iniettato al posto di una variabile viene ritrovato dal walk-forward
(AUC 0,72–0,80), sfasato di 400 giorni no (0,40–0,56): la pipeline è allineata.

**Perché fallisce di nuovo.**
- *La base rate condizionata al regime non corregge il difetto, lo ripete.* Nell'addestramento al 2021 BTC saliva a 30 giorni nel
  65% dei giorni di regime U e nel 54% di quelli misti; dal 2021 è successo il contrario (U 47%, M 72%, D 49%). Da sola la base
  rate del regime ha AUC 0,38–0,43 nel 2021–23. Con 6–10 episodi lunghi per stato, la frequenza "del regime" è la storia di 2–3 cicli.
- *I coefficienti di politica hanno segno stabile ma non prevedono.* A 30 giorni: tasso in salita −, dollaro −, CPI in salita −,
  curva +, rendimento reale −: segno costante nel 100% dei riaddestramenti e identico al racconto comune ("stretta = male").
  Fuori campione però P ha AUC 0,40 nel 2021–23 e 0,56 nel 2024–26: sono relazioni fra POCHE fasi (una per ciclo), stimate su
  migliaia di giorni che non sono indipendenti. La regolarizzazione le porta quasi a zero (λ 1.000–10.000 nel 75% dei casi).
- *Interazioni flusso × regime*: tutte positive e piccole (pf conta un po' di più in U); R non supera il flusso da solo.
- A 7 giorni le variabili di politica (che cambiano in mesi) non possono ordinare esiti settimanali: AUC 0,46 in entrambi i periodi.

## Cosa aggiunge la politica economica al flusso perp
| h | AUC PF → PF+P, 2021–23 | AUC PF → PF+P, 2024–26 | ΔAUC 2021–26 (IC 95%) | Esito |
|---|---|---|---|---|
| 7 | 0,521 → 0,480 | 0,534 → 0,485 | −0,047 (−0,086 / −0,007) | non aggiunge: peggiora |
| 30 | 0,584 → 0,412 | 0,565 → 0,617 | −0,071 (−0,170 / +0,024) | non aggiunge (segno opposto fra i periodi) |

Anche dentro il modello a regimi: RP − R = −0,004 a 7 giorni e +0,016 a 30 giorni (IC −0,05 / +0,10). Coerente con la lezione 96.

## W3.2 (dal 01/01/2021, 10.000 $, 1x, costi; motore p2_engine = radar.weekly.simulate)
| Variante | Finale | Rend. | DD giorn. | Trade | WR | MAR | MAR 2021–23 / 2024–26 | Δ senza i 2 trade | Placebo | Passa |
|---|---|---|---|---|---|---|---|---|---|---|
| Buy & hold | 22.280 $ | +123% | −76,6% | 1 | – | 0,19 | | | | |
| **W3.2** | **78.474 $** | +685% | −21,1% | 13 | 92% | 1,99 | 2,57 / 1,63 | | | |
| A · niente nuovi long con tasso in salita e liquidità netta in calo | 78.474 $ | +685% | −21,1% | 13 | 92% | 1,99 | 2,57 / 1,63 | 0 | – | no (0 eventi) |
| B · esposizione ×0,5 in alta volatilità | 54.531 $ | +445% | −19,3% | 13 | 92% | 1,73 | 1,88 / 1,63 | negativo | 67° | no |
| C · blocco se RP a 30 giorni è contrario | 58.070 $ | +481% | −21,1% | 12 | 92% | 1,65 | 1,77 / 1,73 | negativo | 100° | no |

A non scatta mai: dal 2021 nessun long di W3.2 è nato con politica restrittiva (l'unico segnale in quella condizione è lo short del
14/08/2022): W3.2 evita già da sola i long nel 2022; nel 2018–20 (informativo) A toglie 1 trade (28,0k contro 25,1k, WR 57%).
B dimezza 5 ingressi, fra cui i long del 01/2021 (+52%) e 10/2021 (+21%): costa 24k per 1,8 punti di drawdown. C ritarda il long del 01/2023 al 19/03 (da +13% a −7,5%) e quello del 10/2023 di una settimana (da +40% a +22%); evita il long
perso del 08/2026 (−4,1%), ma il saldo è −20k; nel 2018–20 dimezza il capitale (13,5k contro 25,1k).

## Studio: come si è comportato BTC nelle fasi di politica economica e nei regimi (01/2015 → 11/2026)
**Questa è descrizione (cosa è successo), non previsione.** Riferimento su tutti i 4.337 giorni: rendimento medio a 30 giorni
+6,3% (mediana +3,1%), rialzo a 30 giorni nel 57,9% dei casi, a 7 giorni nel 54,7%. Solo 144 finestre di 30 giorni indipendenti.

**Fasi storiche della Fed (ogni riga è UN solo episodio; date a posteriori).**
| Fase | Tasso Fed | Bilancio (mld $) | BTC nella fase | Media a 30 g | Rialzi a 30 g | DD massimo | Finestre 30 g |
|---|---|---|---|---|---|---|---|
| Tasso a zero, prima dei rialzi (01–12/2015) | 0,13 → 0,15 | 4.510 → 4.480 | +45% | +6,4% | 64% | −46% | 11 |
| Rialzi 2015–18 (QT da 10/2017) | 0,15 → 2,20 | 4.480 → 4.090 | +703% | +9,6% | 60% | −83% | 36 |
| Pausa 2019 | 2,20 → 2,40 | 4.090 → 3.800 | +149% | +16,7% | 79% | −28% | 7 |
| Tagli 2019 (08/2019–03/2020) | 2,39 → 1,58 | 3.800 → 4.160 | −16% | −4,6% | 40% | −45% | 7 |
| Emergenza: tasso zero + QE (03/2020–03/2022) | 1,59 → 0,08 | 4.160 → 8.910 | +370% | +10,5% | 60% | −53% | 24 |
| Rialzi 2022–23 (QT da 06/2022) | 0,08 → 5,08 | 8.910 → 8.270 | −28% | −1,2% | 44% | −67% | 16 |
| Plateau 5,3% + QT (07/2023–09/2024) | 5,08 → 5,33 | 8.270 → 7.120 | +111% | +7,0% | 65% | −26% | 14 |
| Tagli 2024–25 (09/2024–12/2025) | 5,33 → 3,89 | 7.120 → 6.540 | +46% | +3,1% | 53% | −32% | 14 |
| Fermo ~3,6%, bilancio stabile (12/2025–09/2026) | 3,89 → 3,63 | 6.540 → 6.740 | −18% | +0,3% | 61% | −40% | 9 |
| Rialzo di 09/2026 → oggi (60 giorni) | 3,63 → 3,88 | 6.740 → 6.760 | −15% | −7,3% | 13% | −26% | 2 |

Lettura: i due cicli di rialzo danno esiti opposti (+703% nel 2015–18, con dentro sia la bolla 2017 sia il −83% del 2018; −28% nel
2022–23). Il QE 2020–21 coincide con +370%, ma i tagli del 2019 con −16% e quelli del 2024–25 con un modesto +46%. Il QT ha
convissuto con +111% (2023–24). "Stretta = BTC giù" vale per 1 ciclo su 2; "tagli = BTC su" per 1–2 su 3. Sono 2 cicli di rialzo, 3 di
taglio, 1 QE: non c'è statistica possibile, solo storia. È anche ciò che trova Karau (2023): il segno dell'effetto cambia nel 2020.

**Stati meccanici, noti in tempo reale** (episodi = tratti contigui di almeno 30 giorni).
| Stato | Giorni | Episodi ≥ 30 g | Media a 30 g | Mediana | Rialzi a 30 g | Rialzi a 7 g | DD massimo |
|---|---|---|---|---|---|---|---|
| Tasso in RIALZO (su 6 mesi) | 1.613 | 5 | +4,7% | +1,7% | 54% | 52% | −83% |
| Tasso FERMO | 1.941 | 9 | +9,2% | +4,7% | 63% | 59% | −53% |
| Tasso in TAGLIO | 783 | 4 | +2,2% | +0,8% | 52% | 50% | −54% |
| Bilancio in espansione (QE) | 1.037 | 4 | +5,6% | +2,1% | 54% | 54% | −54% |
| Bilancio stabile | 1.669 | 5 | +8,6% | +4,8% | 62% | 56% | −64% |
| Bilancio in riduzione (QT) | 1.631 | 4 | +4,4% | +2,0% | 56% | 53% | −67% |
| Liquidità netta in aumento / in calo (13 sett.) | 2.052 / 2.285 | 17 / 21 | +9,8% / +3,1% | +4,7% / +1,8% | 62% / 55% | 57% / 53% | −54% / −67% |
| Restrittiva: tasso su + liquidità giù | 1.473 | 13 | +2,3% | +1,2% | 53% | 50% | −67% |
| Dollaro in salita / in discesa (3 mesi) | 2.432 / 1.905 | 24 / 20 | +3,9% / +9,2% | +1,5% / +5,3% | 53% / 64% | 54% / 55% | −62% / −59% |
| Rendimento reale in salita / in discesa | 2.247 / 2.090 | 24 / 22 | +5,3% / +7,3% | +2,6% / +3,5% | 57% / 59% | 53% / 56% | −60% / −54% |
| CPI annuo in salita / in discesa | 2.124 / 1.818 | 24 / 23 | +4,9% / +8,1% | +1,3% / +4,7% | 53% / 63% | 54% / 56% | −58% / −46% |
| Curva invertita / positiva | 792 / 3.545 | 1 / 4 | +4,7% / +6,6% | +1,7% / +3,5% | 56% / 58% | 53% / 55% | −35% / −83% |
| VIX > 25 / ≤ 25 | 562 / 3.775 | 5 / 23 | +6,8% / +6,2% | +5,9% / +2,7% | 65% / 57% | 59% / 54% | −49% / −64% |
| FOMC entro 7 giorni / no | 665 / 3.672 | 95 riunioni | +6,2% / +6,3% | +2,2% / +3,3% | 57% / 58% | 51% / 55% | – |
| **Mercato** T=U (sopra SMA200 in salita) | 2.339 | 10 | +8,3% | +3,3% | 57% | 54% | −57% |
| T=M (misto) | 814 | 9 | +6,6% | +5,1% | 64% | 57% | −36% |
| T=D (sotto SMA200 in discesa) | 1.184 | 6 | +2,1% | +1,6% | 55% | 54% | −67% |
| V=A volatilità alta / V=B bassa | 2.016 / 2.291 | 29 / 29 | +8,9% / +4,1% | +4,3% / +1,8% | 63% / 54% | 58% / 52% | −64% / −56% |
| T=D · V=B (ribasso "lento") | 722 | 10 | +0,7% | +0,1% | 50% | 53% | −48% |
| T=U · V=A (rialzo "veloce") | 1.244 | 11 | +10,2% | +4,5% | 59% | 58% | −57% |

**Stabilità nei quattro trienni** (differenza del rendimento medio a 30 giorni fra condizione vera e falsa, punti %; 2015–17 /
2018–20 / 2021–23 / 2024–26): liquidità netta in aumento +10,6 / +10,4 / +2,8 / +2,9 (4/4, in calo); T=D −9,7 / −0,8 / −7,3 /
−3,0 (4/4); volatilità alta +4,1 / +5,1 / +6,4 / +2,2 (4/4); dollaro in salita −10,9 / −5,9 / −5,6 / +0,1; tasso in rialzo +4,3 /
−12,5 / −2,3 / −11,1; rendimento reale in salita +9,6 / −10,1 / −3,3 / −2,5; CPI in salita +0,7 / −1,5 / −6,7 / −5,9; QE n.d. /
+12,0 / −1,0 / −5,5; QT n.d. / −6,8 / +6,5 / +6,2; VIX > 25 −10,5 / +10,5 / −5,2 / +10,7; T=U +12,1 / +3,6 / −1,2 / −2,3.

**Descrizione contro previsione.** Tre condizioni hanno lo stesso segno in 4 trienni su 4 (liquidità netta, ribasso T=D, alta
volatilità). Su 13 condizioni guardate, 1–2 "4 su 4" si ottengono per caso (probabilità 1/8 ciascuna), e riguardano il rendimento
MEDIO (spinto da pochi mesi estremi), non la frequenza di rialzo: 62% contro 55% per la liquidità, 55% contro 57–64% per T=D. Messe
nel modello e giudicate fuori campione non ordinano gli esiti (AUC ≤ 0,50 sul 2021–26), e la liquidità a 28 giorni era già
risultata non significativa in n3 (+0,8 / +1,4 punti, p 0,38 / 0,39). Cosa si poteva sapere prima: lo stato (è noto in tempo
reale); non l'esito. Uso legittimo: contesto ("siamo in una fase che in passato è stata più difficile"), non segnale.

## Stato attuale (dati data/ al 21/11/2026, chiusura 60.216 $; FRED al 19–20/11) · solo esempio
- **Mercato**: T = D (prezzo −17% sotto la SMA200, media in discesa), V = A (volatilità alta). Flusso perp −1,6, W3.2 short dal 16/11.
- **Politica**: tasso in RIALZO (3,88%, +0,25 dal 17/09/2026), bilancio STABILE (6.760 mld), liquidità netta +0,6% in 13 settimane,
  rendimento reale 2,88% (+0,20 in 3 mesi), curva +0,28, dollaro +3,8% in 3 mesi, VIX 28, CPI annuo 3,7% in salita (dato di 09/2026), FOMC fra 18
  giorni (09/12). È la combinazione "restrittiva" del racconto comune; nello storico T=D·V=A ha dato +4,7% medio e 65% di rialzi
  a 30 giorni (7 episodi), "tasso in rialzo + bilancio stabile" +7,4% e 56% (6 episodi): nessuna indicazione utilizzabile.
- **Probabilità dei modelli (senza capacità dimostrata)**: 7 giorni R 49,5%, P 54,4%, RP 50,5% (base del regime 53,7%); 30 giorni
  R 54,6%, P 57,3%, RP 51,5% (base del regime 55,3%); solo flusso 47,5%. Tutte nel terzo basso delle previsioni passate nello stesso
  regime ("giù" relativo): dicono "meno del solito", in accordo con lo short di W3.2, senza aggiungere informazione provata.

## Limiti e deviazioni dal PREREG
- Periodo di giudizio già guardato nel primo ciclo; le 4 variabili "stabili" erano state scelte guardando il 2021–26: se qualcosa
  fosse passato sarebbe stato comunque da confermare dal vivo. Non è passato nulla.
- Deviazioni: (1) p2_sanity.py (segnale iniettato) aggiunto dopo, non preregistrato; (2) scarico FRED con curl (requests non
  attraversa il proxy del container): tutte le 11 serie scaricate, nessuna mancante; date FOMC 2015–20 trascritte dalle pagine
  storiche della Fed (2015 ricontrollato sulla pagina), dal 2021 file di n3; (3) variante A: 0 eventi dal 2021, quindi identica a
  W3.2 e non valutabile (placebo non significativo per costruzione); (4) i confronti con persistenza e W3.2 sono sui giorni in cui
  entrambi danno una previsione; (5) vicini non eseguiti (nessuna variante passa); (6) le fasi storiche della parte descrittiva
  hanno date fissate dopo aver letto DFF, come previsto dal PREREG §7; (7) il CPI di 10/2025 manca nella serie (non pubblicato):
  mancano quindi i CPI annui di 10/2025 e 10/2026 e si porta avanti l'ultimo valore pubblicato (oggi: 09/2026). Nessuna variabile, soglia, regime o modello cambiato dopo i risultati.
- Dati FRED all'ultima revisione (non le annate ALFRED), usati con i ritardi dichiarati: DFF 2 giorni; WALCL e WTREGEN dal venerdì;
  RRP, rendimenti e VIX 1 giorno; dollaro 8 giorni; CPI dal 25 del mese successivo. M2 e S&P 500 non usati nei modelli.
- Non ripetuti (esiti citati): liquidità netta a 28 giorni, FOMC a eventi, stablecoin, premio Coinbase (n3, lezione 96);
  probabilità a celle (lezione 97); VIX ed EMA200 come regola (lezione 104).

## Lezione proposta (113)
**Lezione 113**: adattare il previsionale ai regimi di mercato (trend su SMA200, volatilità) e alla politica economica (tasso Fed,
liquidità netta, rendimento reale, curva, dollaro, VIX, FOMC, CPI; FRED dal 2015 con i ritardi di pubblicazione) non lo fa
funzionare: AUC fuori campione 0,46–0,53 a 7 giorni e 0,40–0,59 a 30 giorni, mai ≥ 0,55 in entrambi i periodi, 0/6 modelli, Holm 1,00
su 16 test dei due cicli; la base rate per regime ripete il difetto dell'intercetta (AUC 0,38–0,43 nel 2021–23: i regimi che
rendevano fino al 2020 hanno reso meno dopo). La politica economica aggiunta al flusso perp lo PEGGIORA (ΔAUC −0,05 a 7 giorni, IC
sotto zero; −0,07 a 30 giorni). Su W3.2 0/3 (il filtro "politica restrittiva" non scatta mai: W3.2 evita già quei long). Le fasi
della Fed sono 1 episodio ciascuna e si contraddicono (rialzi 2015–18 +703%, 2022–23 −28%; tagli 2019 −16%): descrivono, non
prevedono. Regime e politica vanno mostrati solo come contesto. Non riproporre modelli di direzione a 7–30 giorni su regimi o
macro; resta valida solo la misura dal vivo con forecast_log.py. research/previsionale2/ (PREREG 3a6a973).

## Raccomandazione per la dashboard
1. Nessuna probabilità a 7/30 giorni, nemmeno "condizionata al regime".
2. Sì a un riquadro di **contesto** (i dati di macro.py ci sono già in parte; servono DFF e WALCL da FRED), con dicitura fissa:
   "Contesto, non segnale. Mercato: ribasso (prezzo sotto la media a 200 giorni in discesa), volatilità alta. Fed: tasso in
   rialzo (3,88%), bilancio stabile, prossima riunione il 09/12. Dal 2015 queste condizioni non hanno anticipato la direzione di
   BTC a 7–30 giorni (studio del 23/11/2026); la posizione la decide W3.2."
3. Non mostrare medie storiche per fase come attesa ("in questa fase BTC fa +X%"): poggiano su 1–10 episodi.

File: PREREG.md, p2_fetch.py, p2_data.py, p2_run.py, p2_descr.py, p2_w32.py, p2_oggi.py, p2_sanity.py, risultati.txt,
risultati_descrittiva.txt, risultati_w32.txt, risultati_sanita.txt, tabella2.csv, descrittiva*.csv, w32_varianti2.csv,
prob2_h*.csv, coef2_h*.csv, oggi.json, data/ (FRED e date FOMC).
