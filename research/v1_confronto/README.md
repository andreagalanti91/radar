# v1 · voto di 17 indicatori contro W3.2 · BTC · 25/11/2026

**Verdetto: la v1 non vale come strategia operativa né come affiancamento a W3.2. Al massimo può stare nel tool come confronto
informativo, marcato "non in uso", se l'utente vuole vederla.** Nel periodo che la v1 non ha mai visto (2022–26) fa 21.826 $ contro
43.970 $ di W3.2, con drawdown −34% contro −21%. Il 50% W3.2 + 50% v1 a capitali separati abbassa il CAGR in ogni periodo tranne il
2018–21 (dove sono state scelte le soglie della v1) e non riduce il drawdown (dal 2021 −20,7% contro −21,1%). Tolte le 3 operazioni
migliori, la v1 vale ×1,05 dal 2018, W3.2 ×6,1. Il verdetto non cambia con la versione di W3.2 calcolata dall'utente. W3.2 resta
invariata. Nessuna modifica al tool.

## Cosa è stato fatto
- **v1**: `import/v1.py` dell'utente usato così com'è (regole, soglie e costi non toccati), su `data/spot.csv` (giorni chiusi) +
  `data/funding.csv` di Radar e `btc_giornaliero.csv` solo prima del 01/09/2019.
- **W3.2 dal 2018**: `radar.weekly.simulate` invariato sul frame lungo della ricerca (`research/p2_nuovi/data/f_long.csv.gz`,
  congelato al 15/11), più i giorni successivi presi da `build_features(data/)`. Dati fino al 21/11/2026 (ultimo giorno in `data/`).
- Periodi: ognuno è un tratto della serie continua, riportato a 10.000 $ (le posizioni aperte all'inizio si ereditano). 50/50 =
  metà del capitale per ciascuna, conti separati, mai ribilanciati.
- Nessun PREREG: non si sceglie niente. Le soglie vicine (±0,05 e ±0,10) servono solo a descrivere la robustezza.
- Script: `s1_riproduzione.py`, `s2_w32.py`, `s3_confronto.py` (→ `risultati.txt`, `tab_*.csv`), `s4_extra.py` (→
  `risultati_extra.txt`). Durata totale meno di un minuto.

## 1. Riproduzione della v1: sì
| | Finale | Operazioni | Short | CAGR | DD |
|---|---|---|---|---|---|
| File dell'utente (al 22/11) | 184.406 $ | 30 | 7 | +38,8% | −49,4% |
| Dati di Radar (al 21/11) | 184.406 $ | 30 | 7 | +38,8% | −49,4% |

Le 30 operazioni coincidono con `v1_operazioni_2018_2026.csv`. I voti dal 2018 sono identici (differenza 0). I prezzi sono identici.
Il volume differisce in 10 giorni del 2021–22 (al massimo 2.025 BTC, dati rivisti), ma il voto dell'OBV non cambia. Il 22/11 la v1
è fuori, quindi il giorno in più del file dell'utente non sposta il risultato.

## 2. W3.2 dal 2018: due versioni
| Versione | Finale (al 21/11) | DD | Operazioni |
|---|---|---|---|
| **Radar**: `weekly.simulate` continuo dal 2018 | **241.439 $** | −37,3% | 23 |
| Utente: 2018–20 chiuso al 31/12/2020 e unito a "dal 2021" | 212.098 $ (209.002 $ al 22/11) | −37,3% | 23 |
| Controllo: lo stesso motore sui dati congelati al 15/11 | 224.593 $ (come in research/utxo_pl) | −37,3% | 22 |

Confronto operazione per operazione: 22 delle 23 operazioni hanno stesse date, prezzi, esposizioni e risultati (differenze ≤ 0,06
punti). Le differenze sono soltanto due:
1. **La giunzione al 31/12/2020 (circa −12% sul finale).** Nella versione dell'utente il long del 14/12/2020 si chiude d'ufficio
   il 31/12/2020 a 28.924 $ (+50,4% sul capitale). Nella serie continua resta aperto fino all'uscita per distribuzione del
   04/01/2021 a 32.967 $ (+71,5%). Il rapporto 1,715/1,504 = 1,14 spiega tutta la differenza: il 2021 fa +91,9% per l'utente e
   +118,4% per Radar. Dal 2021 l'utente riparte da flat (84.360 $, il numero del tool). Il tratto "dal 2021" della serie continua
   vale invece 94.693 $, perché eredita quel long.
2. **Il giorno finale.** L'utente arriva al 22/11 (61.271 $), `data/spot.csv` al 21/11 (60.215 $). Lo short aperto vale +5,9%
   nella versione dell'utente e +7,5% in quella di Radar. Allo stesso giorno le due curve coincidono.

Non ci sono differenze di flusso, date o costi. In entrambe le versioni il flusso è stimato dal CVD spot soltanto fino
all'11/04/2020; dal 12/04/2020 è il pf14z reale. Le due operazioni perdenti del 2020 (long 10/02, −2,6%; short 16/03, −17,9%)
compaiono in entrambe le versioni. Il "2018–2020 tutto con flusso stimato" scritto nel prompt è quindi impreciso. Da notare: un
primo tentativo con `data/` unito al frame lungo al 01/09/2019 lasciava il flusso vuoto fra settembre 2019 e aprile 2020. Quella
variante perde le due operazioni del 2020 e fa 301.868 $: è un errore di unione, scartato. Per il confronto si usa la versione
Radar. La versione dell'utente è riportata accanto.

## 3. Confronto (10.000 $, 1x, costi inclusi, fino al 21/11/2026)
| Periodo | Strategia | Finale | CAGR | DD | Sharpe | Operazioni | In guadagno | Perdita peggiore |
|---|---|---|---|---|---|---|---|---|
| **Tutto 2018→** | **W3.2** | **241.439** | +43,1% | −37,3% | 1,30 | 23 | 78% | −25,1% |
| | v1 | 184.406 | +38,8% | −49,4% | 0,95 | 30 | 47% | −20,6% |
| | 50/50 | 212.922 | +41,1% | −44,7% | 1,13 | – | – | – |
| | Buy & hold | 45.004 | +18,4% | −81,2% | 0,59 | – | – | – |
| | *W3.2 utente / 50/50* | *212.098 / 198.252* | *+41,0 / +39,9%* | *−37,3 / −44,7%* | *1,26 / 1,10* | | | |
| **2018–21** (soglie v1) | W3.2 | 54.910 | +53,1% | −37,3% | 1,50 | 12 | 67% | −25,1% |
| | **v1** | **84.489** | +70,6% | −49,4% | 1,27 | 11 | 55% | −20,6% |
| | 50/50 | 69.700 | +62,5% | −44,7% | 1,38 | – | – | – |
| | *W3.2 utente* | *48.237* | *+48,2%* | *−37,3%* | | | | |
| **2022–26** (mai visto dalla v1) | **W3.2** | **43.970** | +35,4% | −21,1% | 1,13 | 11 | 91% | −4,1% |
| | v1 | 21.826 | +17,3% | −34,3% | 0,61 | 19 | 42% | −19,2% |
| | 50/50 | 32.898 | +27,6% | −20,7% | 0,94 | – | – | – |
| | Buy & hold | 12.618 | +4,9% | −66,9% | 0,35 | – | – | – |
| **Dal 2021** | **W3.2** | **94.693** | +46,5% | −21,1% | 1,39 | 14 | 93% | −4,1% |
| | v1 | 46.181 | +29,7% | −34,3% | 0,83 | 21 | 48% | −19,2% |
| | 50/50 | 70.437 | +39,3% | −20,7% | 1,17 | – | – | – |
| | *W3.2 utente / 50/50* | *84.360 / 65.271* | *+43,7 / +37,5%* | *−21,1 / −20,7%* | | | | |
| **Ultimi 12 mesi** | **W3.2** | **12.197** | +22,0% | −18,3% | 0,79 | 4 | 75% | −4,1% |
| | v1 | 7.570 | −24,3% | −31,7% | −0,67 | 4 | 25% | −9,2% |
| | 50/50 | 9.884 | −1,2% | −20,0% | 0,11 | – | – | – |
| | Buy & hold | 7.073 | −29,3% | −39,5% | −0,56 | – | – | – |

Dal 2022 in poi le due versioni di W3.2 coincidono. Per sottoperiodi: nel 2021–23 W3.2 fa 37.578 $ (DD −19%) e la v1 30.498 $
(−32%); dal 2024 W3.2 fa 25.250 $ (−21%) e la v1 14.492 $ (−34%).

**Anno per anno**
| | 2018 | 2019 | 2020 | 2021 | 2022 | 2023 | 2024 | 2025 | 2026 |
|---|---|---|---|---|---|---|---|---|---|
| W3.2 | −9,7% | +41,5% | +96,7% | +118,4% | +19,4% | +46,1% | +102,7% | +4,9% | +18,5% |
| v1 | +3,1% | +61,5% | +136,5% | +114,6% | +2,9% | +40,0% | +65,4% | +16,4% | −21,3% |
| Buy & hold | −72,3% | +94,3% | +302,0% | +59,8% | −64,2% | +155,6% | +121,3% | −6,3% | −31,3% |

La v1 fa meglio di W3.2 nel 2018, 2019, 2020 e 2025. Nella versione dell'utente W3.2 fa +91,9% nel 2021.

**Senza le operazioni migliori** (prodotto dei risultati sul capitale)
| | Tutto: con tutte / senza la migliore / senza le 3 migliori | 2022–26 | Dal 2021 |
|---|---|---|---|
| W3.2 | ×24,1 / ×14,1 / **×6,1** | ×4,40 / ×3,09 / **×1,68** | ×8,43 / ×5,54 / **×2,77** |
| v1 | ×18,5 / ×4,1 / **×1,05** | ×2,22 / ×1,14 / **×0,62** | ×2,68 / ×1,38 / **×0,75** |

La migliore operazione della v1 (long 10/2020→04/2021, +357%) vale da sola tre quarti del risultato.

**Quando sono d'accordo** (2018→oggi, 3.247 giorni; rendimento annualizzato nei giorni di ogni stato)
| Stato | Giorni | BTC | W3.2 | v1 |
|---|---|---|---|---|
| Entrambe long | 929 (29%) | +216% | +170% | +215% |
| Entrambe short | 223 (7%) | −16% | −1% | −16% |
| Entrambe fuori | 920 (28%) | −39% | 0% | −1% |
| Solo W3.2 in posizione | 584 (18%) | +7% | **+53%** | −1% |
| Solo v1 in posizione | 588 (18%) | −14% | 0% | **+5%** |
| Versi opposti | 3 (0,1%) | – | −2,0% (totale) | +6,2% (totale) |

Nel 2022–26: quando è in posizione solo W3.2, W3.2 rende +98% annuo; quando è in posizione solo la v1, la v1 rende +12% annuo.
Quando sono entrambe short, W3.2 rende −35% e la v1 −63% annuo (in quei giorni BTC è salito). Correlazione dei rendimenti
giornalieri: 0,65 su tutto il periodo, 0,64 nel 2022–26, 0,72 negli ultimi 12 mesi (mensile 0,73).

**Robustezza della v1** (descrittiva, non serve a scegliere)
- Soglie vicine, 125 combinazioni di long/short/uscita a ±0,05/±0,10: mediana 124.717 $ dal 2018 (da 27.290 a 213.876 $), DD
  mediano −58,7%. Nel 2022–26 la mediana è 20.655 $. **Nessuna combinazione batte W3.2** né sul periodo intero né nel 2022–26 né
  dal 2021. Le soglie in uso stanno nella parte alta della famiglia, come ci si aspetta da soglie scelte sul 2018–21. Lo short è
  fragile: a −0,85 o −0,80 il risultato scende a 64–59k $ (DD −68%).
- Esecuzione con ritardo: con un giorno in più 125.838 $, con due 75.579 $ (2022–26: 16.381 e 12.914 $).
- Placebo, posizione della v1 spostata in blocco nel tempo (1.000 spostamenti): dal 2018 p = 0,021; nel 2022–26 p = 0,11. Nel
  periodo mai visto la v1 non si distingue da un tempismo casuale con la stessa esposizione.
- A parità di drawdown con W3.2 (v1 a 0,59x dal 2021): 27.857 $ contro 94.693 $. Dal 2018 (0,71x): 95.227 $ contro 241.439 $.
- 50/50 ribilanciato ogni giorno, come nel confronto dell'utente (223.979 $): 240.440 $ dal 2018 con W3.2 di Radar, comunque
  sotto W3.2 da sola. Dal 2021 fa 71.449 $ (DD −21,3%), nel 2022–26 32.665 $. Il guadagno sul periodo intero viene dal
  ribilanciamento del 2018–20, non dalla v1.

## Cosa dicono i dati
- La v1 batte W3.2 solo dove ha scelto le soglie (2018–21). Nei cinque anni mai visti rende la metà, con un drawdown più ampio e
  il 42% di operazioni in guadagno. Nel 2026 perde il 21%.
- Le due strategie sono long insieme quasi sempre nei grandi rialzi. La differenza viene dai giorni in cui ne lavora una sola:
  W3.2 da sola guadagna +53% annuo, la v1 da sola +5%. I segnali "in più" della v1 sono rumore. Lo short della v1 (−0,90)
  scatta tardi, spesso sui minimi.
- La combinazione non aggiunge diversificazione utile, perché la correlazione è 0,65 e la v1 è più debole. Il 50/50 sta sotto
  W3.2 in CAGR in ogni periodo tranne il 2018–21, con un drawdown uguale (dal 2021) o peggiore (dal 2018: −44,7% contro −37,3%).
- Come informazione la v1 riassume medie, MACD, RSI, Donchian e OBV. Questi indicatori sono già stati provati uno per uno e
  come voto (lezioni 86, 117, 119): non aggiungono nulla a W3.2. Mostrarla ha valore didattico, non decisionale.

## Limiti
- Il 2022–26 è fuori campione solo per la v1. Le regole di W3.2 (filtro F1, rischio 25%, flusso a 3 giorni) sono state decise
  nel novembre 2026 guardando tutto il 2018–26. Il vantaggio di W3.2 nel 2022–26 va quindi scontato: il dato onesto per W3.2
  sono solo le settimane dal vivo, dal 02/11/2026.
- W3.2 nel 2018–11/04/2020 usa un flusso stimato. Nel 2018–19 non ha funding (0), mentre la v1 accredita agli short lo 0,03%
  al giorno.
- Costi un po' diversi: W3.2 usa quelli di Radar (commissione + slittamento all'apertura del lunedì), la v1 lo 0,10% per lato
  alla chiusura. La v1 esegue alla stessa chiusura del segnale, che dal vivo non è raggiungibile in modo esatto: con un giorno di
  ritardo perde un terzo del finale.
- W3.2 ha esposizione 0,4–1x, la v1 sempre 1x. Il confronto a pari drawdown corregge questo punto e lascia la v1 molto sotto.
- 23 e 30 operazioni: le percentuali di operazioni in guadagno sono stime grossolane.

## Lezione 126 proposta per RESEARCH.md
**Lezione 126**: la "v1 · voto di 17 indicatori" dell'utente (trend, momentum, rottura e OBV giornalieri e settimanali; long ≥
+0,50, short ≤ −0,90, uscita a ±0,25; research/v1_confronto) si riproduce esattamente (184.406 $ dal 2018, 30 operazioni, anche
con i dati di Radar). Batte W3.2 solo nel 2018–21, dove sono state scelte le soglie (84,5k contro 54,9k $). Nel 2022–26, mai
visto, fa 21,8k $ (DD −34%, 42% in guadagno) contro 44,0k $ (DD −21%) di W3.2. Senza le 3 operazioni migliori vale ×1,05 dal
2018 (W3.2 ×6,1). Placebo nel 2022–26 p 0,11; 0 combinazioni su 125 di soglie vicine sopra W3.2; con un giorno di ritardo −32%. Il
50/50 a capitali separati abbassa il CAGR senza ridurre il DD (correlazione 0,65). Nei giorni in cui è in posizione solo lei, la v1
rende +5% annuo, W3.2 da sola +53%. W3.2 dal 2018 con `weekly.simulate` continuo fa 241.439 $; i 209.002 $ dell'utente vengono
dalla chiusura d'ufficio del long al 31/12/2020 (−12%) e da un giorno di dati in più, non da flusso, date o costi. Un voto di
indicatori di prezzo non aggiunge informazione al flusso perp (conferma delle lezioni 86, 117 e 119). Al massimo un confronto
informativo "non in uso", mai una strategia o un affiancamento. Nei confronti di lungo periodo W3.2 va simulata continua: cucire
due periodi chiudendo le posizioni sposta il risultato in modo rilevante. Quando si uniscono frame, va controllato che il flusso
non resti vuoto (un'unione al 01/09/2019 cancellava le operazioni del 2020).
