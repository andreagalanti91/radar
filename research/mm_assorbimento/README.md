# Effetti dei market maker: assorbimento e compressione → rottura (BTC 1h/4h) · 18/11/2026 · RESPINTO

Preregistrazione: PREREG.md (commit separato, prima di qualsiasi script). Regole, parametri e soglie non modificati.

## Conclusione
Le 18 configurazioni preregistrate (A1, A2, B1, B2, C1, C2 con 2 vicini ciascuna) non fanno **nessun trade** dal 2022-02 al
17/11/2026. Il motivo: la barra di "assorbimento" come definita (volume ≥ 80° percentile e range ≤ 30° percentile su 30 giorni)
su BTC quasi non esiste, perché volume e range orari vanno insieme (correlazione dei logaritmi 0,76 su 1h e 0,67 su 4h).
In 4,7 anni ci sono 6 barre orarie così e nessuna ha anche il delta concorde e l'OI in aumento; su 4h ce ne sono 3, nessuna valida.
Tutte le regole dipendono dall'assorbimento (le B e le C usano A1 come filtro), quindi non c'è niente da giudicare.
I controlli che ne fanno a meno perdono dopo i costi in entrambe le metà:
- **K0** (compressione di 24 ore e rottura): 10k → 6,5k, DD −44%.
- **K1** (rottura delle 24 ore senza compressione): 10k → 3,7k, DD −74%.

## Tabella (10.000 $ al 01/01/2021, 1x, costi 0,13% per lato e funding reale; regole attive dal 2022-02-01)
| Regola | Capitale | Rend. | DD giorn. | Trade | WR | PF IS / OOS | MAR |
|---|---|---|---|---|---|---|---|
| A1, A2, B1, B2, C1, C2 (e i 12 vicini) | 10.000 $ | 0% | 0% | 0 | — | — | — |
| K0 compressione 24h → rottura | 6.484 $ | −35,2% | −44,3% | 558 | 46,8% | 0,96 / 0,95 | −0,79 |
| K1 rottura 24h | 3.686 $ | −63,1% | −73,7% | 749 | 46,6% | 0,85 / 0,98 | −0,86 |
| K0 + verso della mappa (I ≥ 0,10, info) | 5.623 $ | −43,8% | −54,7% | 429 | 48,5% | 0,84 / 0,96 | −0,80 |
| W3 (radar/weekly.simulate) | 78.838 $ | +688% | −21,1% | 14 | 93% | — | 32,6 |
| Buy & hold | 22.455 $ | +124,5% | −76,6% | — | — | — | 1,63 |

Dal 2022-02-01 (quando partono le regole): buy & hold 16.884 $ (DD −66,7%), W3 36.663 $ (DD −21,1%).
MAR = rendimento totale / |DD|.

## Robustezza (solo sui controlli: le regole non hanno trade)
- **IS e OOS.** K0 media per trade −0,044% / −0,052%, K1 −0,201% / −0,024%. Nessuna metà è positiva.
- **Senza i 5 trade migliori.** K0 scende a 4.855 $, K1 a 2.352 $.
- **Placebo.** Ingressi casuali con la stessa geometria finiscono in mediana a 1.990 $ (K0) e 1.138 $ (K1), quindi le rotture fanno meglio del caso (p 0,012 e 0,042). Nessuno dei due p è sotto la soglia di Bonferroni (0,0028), e i controlli non erano comunque ammissibili. Le rotture hanno un po' di momentum, ma non bastano a coprire i costi.
- **Mappa delle liquidazioni.** Filtrare K0 nel verso del lato più carico peggiora il PF da 0,95 a 0,91 (conferma la lezione 93).
- **Uscite alternative (informative).** Target sempre a 2·W, tempo massimo 24h o 72h: tutte in perdita, tranne K1 a 72h che arriva a PF 1,05 (10,6k, DD −57%). È un caso isolato su più di 20 prove.
- **Dal 2021-01-22.** K0 scende a 3.140 $ (DD −73%), K1 a 420 $.
- **Effetto su W3.** C1 e C2 non fanno trade, quindi W3 resta invariata a 78.838 $.

## Diagnostica (diag.txt, solo conteggi, nessun rendimento)
| | 1h | 4h |
|---|---|---|
| volume ≥ 80° e range ≤ 30° | 6 | 3 |
| … e anche |D| ≥ 0,10, delta concordi, ΔOI > 0 | 0 | 0 |
| volume ≥ 80° e range ≤ 50° (non testato) | 84 | 31 |
| volume ≥ 70° e range ≤ 50° (non testato) | 419 | 128 |

## Verdetto per regola
| Regola | Esito |
|---|---|
| A1, A2, B1, B2 | RESPINTA: 0 trade, criterio 1 non soddisfatto |
| C1, C2 | SENZA POTENZA: 0 trade, W3 invariata |
| Effetto su W3 | Nessuno |

La verifica su ETH e SOL non è stata fatta, perché nessuna regola è stata accettata.

## Deviazioni dal PREREG (nessuna sulle regole)
1. **Cache estese.** Le cache sono state estese con sq_data.py --refresh dopo aver scaricato gli archivi Binance 13–17/11. Le candele perp e l'OI coprono fino al 17/11 23:00 (nessuna ora spot usata); le mappe arrivano al 18/11.
2. **Ore mancanti.** Le 24 ore mancanti del 28/10/2026 sono riempite con barre piatte: nessun segnale e nessun percentile in quelle ore.
3. **W3 di riferimento.** W3 vale 78.838 $ e non 78.474 $: è la stessa funzione, con i dati fino al 17/11 e lo short aperto valutato al prezzo corrente.
4. **Giorni flat di W3.** Il giorno di un'uscita all'apertura (EMA o distribuzione) conta come flat; il giorno di uno stop o di un trailing no.
5. **Target sulla fascia.** Si usa la fascia densa più vicina a distanza ≥ W. Se è oltre 3·W il target è 2·W, senza cercare la fascia successiva.
6. **Placebo.** I trade non si sovrappongono perché si estraggono finestre di 48 ore. Per C1 e C2 il placebo non è stato eseguito (0 trade).
7. **File dei trade.** Le regole senza trade non scrivono il proprio file.

## File
PREREG.md · mm_data.py (dati, cache /tmp/radar-work/mm/feat.pkl) · mm_bt.py (motore e regole) · mm_placebo.py ·
mm_run.py → risultati.txt, riepilogo.csv, vicini.csv, sensibilita.csv, w3.csv, trades_K0.csv, trades_K1.csv · mm_diag.py → diag.txt.

## Lezione proposta (98)
**Lezione 98**: su BTC la "barra di assorbimento" dei market maker, cioè volume alto e range basso (80°/30° percentile su 30 giorni),
quasi non esiste su 1h e 4h. Volume e range si muovono insieme (correlazione 0,76): ci sono 6 barre orarie in 4,7 anni e nessuna
con il delta taker concorde e l'OI in aumento. Le regole di assorbimento, compressione filtrata e complementari a W3 non fanno
nessun trade. La compressione oraria → rottura con target sulle fasce di liquidazione (K0) e la rottura delle 24 ore (K1) perdono
dopo i costi in entrambe le metà (PF 0,95 e 0,93; 10k → 6,5k e 3,7k). Fanno meglio di ingressi casuali con la stessa geometria
(p 0,01–0,04), ma non coprono i costi, e il verso della mappa peggiora il risultato. Conferma le lezioni 81, 82, 93 e 95. Un
assorbimento "relativo" (volume alto rispetto al range atteso) richiede una nuova preregistrazione, con aspettativa bassa.
