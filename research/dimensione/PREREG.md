# PREREG · Dimensione ridotta di W3.2 nei casi "affollato", "giovane" e "short tardo" · 27/11/2026

Stato: FASE 1 chiusa (definizioni, conteggi, criteri). Nessun rendimento di variante calcolato. Da committare INSIEME a
`regole.py` e `conteggi.py`, prima di qualsiasi script della fase 2 (errori operativi, lezione 132).

## 1. Idea e ipotesi
Dalla revisione critica (approvata dall'utente) e dall'analisi delle 11 perdite (research/dati_nuovi/errori/): bloccare gli
ingressi fa perdere i trend (lezione 132: i filtri A costano su BTC), quindi si **riduce la dimensione** dell'operazione invece di
saltarla. Ipotesi: nei long "affollati" (leva in crescita forte o funding estremo) e nei long "giovani" (prime settimane sopra la
SMA40) e negli short aperti dopo un crollo, il rapporto guadagno/perdita è peggiore della media; dimezzare il rischio su di essi
migliora CAGR/DD senza ridurre in modo rilevante il capitale finale.
W3.2 (radar/weekly.py) non cambia: segnali, uscite, stop, trailing identici. Cambia solo R allo stop iniziale dell'operazione.

## 2. Motore e dati
- Motore: `regole.sim` = `radar.weekly.simulate` avvolto (come research/dati_nuovi/motore.py), R 0,25, stop/trailing 2,5 ATRw.
  Verifica senza regola e con regola mai vera: BTC dal 2018 242.755 $, BTC dal 2021 84.820 $, ETH dal 11/01/2021 39.572 $ (OK).
- Dimensione ridotta: R = 0,125 invece di 0,25, esposizione = min(1, R / (2,5·ATRw/chiusura)). Sui long con stop < 25% del
  prezzo l'esposizione scende meno della metà (es. 1,00 → 0,59–0,69); riportato in `conteggi_output.txt`.
- Controllo fatto: con la dimensione ridotta le operazioni sono identiche (stesse date di segnale, entrata, uscita, motivo) in
  tutte le varianti e i vicini, come atteso (la dimensione non entra in nessuna decisione).
- Frame: BTC dal 2018 `w32_ufficiale/f_lungo`, BTC dal 2021 `f_tool`, ETH `w32_asset2` (cfeats). Fine 24/11/2026.

| Dato | Fonte | Disponibile alla domenica | Buchi |
|---|---|---|---|
| OI Binance (USD), variazione a 28 g | data/metrics.csv, data/eth_metrics.csv | valore del sabato (ritardo 1 g) | dal 30/12/2021; soglia p90 (≥ 180 g) dal **28/06/2022** |
| Funding 7 g (fund7 di W3.2) | funding giornaliero dei frame | sì (come la distribuzione) | dal 01/01/2020; soglia p90 dal **05/07/2020** |
| Età del trend, SMA40 | prezzo settimanale | sì | BTC completo; ETH SMA40 dal 31/05/2020 |

Conseguenze dichiarate: D1 **non può toccare nessuna operazione prima del 07/2020** (fra cui il caso-guida BTC 07/01/2018,
−25,1%) e fino al 06/2022 usa solo il funding. Dato mancante = nessuna riduzione.

## 3. Varianti (4) e parametri, fissati senza griglia
| # | Regola (alla domenica del segnale) | Lato | Parametro · vicini | Motivazione della soglia |
|---|---|---|---|---|
| **D1** affollato | OI USD a 28 g > p90 dei 365 g precedenti **oppure** fund7 > p90 dei 365 g precedenti **e** > 0,0003/g | long | p90 · p80, p95 | p90 = stessa soglia di V5 FUNDING-A (dati_nuovi) e convenzione "estremo dell'ultimo anno"; percentile mobile invece di "+X%" perché l'OI in USD cresce col prezzo e i livelli BTC/ETH differiscono (stessi parametri su tutti gli asset) |
| **D2** giovane | trend_age ≤ 3 (settimane consecutive sopra la SMA40) | long | 3 · 2, 4 | 6 long persi su 8 nelle prime 1–3 settimane (analisi errori, IS descrittivo già noto); trend_age è la stessa misura di F1 |
| **D3** | D1 ∪ D2 | long | (p90, 3) · (p80, 2), (p95, 4) | combinazione delle due ipotesi |
| **D4** short tardo | chiusura/SMA40 − 1 < −35% | short | 35% · 30%, 40% | 3 short persi aperti al −38/−43% (IS descrittivo già noto); 35% indicato nell'idea |

Correzione fatta **dopo i conteggi e prima di qualsiasi rendimento**: nella bozza la condizione funding era solo "> p90". Uscendo
da un bear (gennaio 2023) il funding al tasso neutro di Binance (0,01% ogni 8 h = 0,0003/g, premio zero) superava il p90
dell'anno precedente: non è affollamento. Aggiunto "e > 0,0003/g" per ragione meccanica. Effetto sui conteggi: BTC 2026-08-23
non è più toccato (era una perdita nota, −4,1%: la correzione va contro l'ipotesi, non a favore). BTC 2023-01-22 resta toccato
(per l'OI). Tutte le 7 operazioni toccate da D1 scattano per l'OI; il funding scatta solo su ETH 2023-01-22 (insieme all'OI).
Non aggiunta l'età del trend a D1 ("vecchio E affollato"): F1 filtra già i trend ≥ 16 settimane e sarebbe una quinta scelta;
il caso BTC 2018 resterebbe comunque fuori per mancanza di OI e funding.

## 4. Conteggi (operazioni toccate, aperta inclusa; dettaglio in conteggi_output.txt / conteggi.csv)
| Variante | BTC dal 2018 | BTC dal 2021 | ETH dal 2021 | Anni (BTC 2018 · ETH) |
|---|---|---|---|---|
| D1 p90 | 3/16 long | 3/9 | 4/10 | 2023, 2024, 2025 · 2023, 2024 ×2, 2026 |
| D1 vicini p80 · p95 | 6 · 2 | 6 · 2 | 4 · 3 | |
| D2 ≤ 3 sett. | 9/16 | 6/9 | 6/10 | 2018, 2020 ×2, 2021 ×2, 2023–2026 · 2022–2026 |
| D2 vicini 2 · 4 | 7 · 10 | 5 · 6 | 6 · 6 | |
| D3 | 10/16 | 7/9 | 7/10 | |
| D3 vicini | 11 · 11 | 9 · 7 | 7 · 7 | |
| D4 −35% | 1/7 short (2020) | 0/5 | 2/5 (2022 ×2) | |
| D4 vicini 30% · 40% | 2 · 1 | 1 · 0 | 2 · 1 | |

Casi-guida: BTC 07/01/2018 non toccato da nessuna variante (dati); ETH 02/06/2024 toccato da D1 e D3, non da D2.
D2 e D3 riducono la maggior parte dei long (fino a 9/9 nel vicino D3): sono vicine a un "rischio più basso per tutti i long",
il caso che la lezione 101 chiede di controllare (vedi §5, criteri 3 e 5).

## 5. Criteri (tutti necessari), confronto con W3.2 com'è
10.000 $ per asset a 1x, costi e funding inclusi, partenza da flat. Insieme = BTC (f_tool) + ETH, 10.000 $ ciascuno dal
11/01/2021. DD giornaliero. CAGR/DD = CAGR / |max DD|.
1. **CAGR/DD più alto e DD non peggiore** di W3.2 su BTC dal 2018, BTC dal 2021, ETH dal 2021 e insieme. Un periodo in cui la
   variante non tocca nessuna operazione è neutro (identico, non conta né a favore né contro).
2. **IS/OOS**: CAGR/DD non peggiore di W3.2 in IS (BTC 2018–2022, ETH 2021–2022) e in OOS (2023→, BTC e ETH), con la stessa
   regola del periodo neutro.
3. **Capitale finale insieme** non più basso di W3.2 di oltre il 5%.
4. **Vicini**: entrambi i vicini rispettano il criterio 1 su insieme e BTC dal 2018 e il criterio 3.
5. **Placebo**: si dimezza R su operazioni scelte a caso, stesso lato, stesso numero per asset di quelle toccate nella finestra
   dell'insieme (dal 11/01/2021); 5.000 prove, seme 20261127; statistica CAGR/DD insieme; p = (1 + #{placebo ≥ reale}) / 5.001.
   Si riporta anche la quota di prove casuali che batte W3.2 (se la maggior parte delle riduzioni casuali migliora W3.2,
   il guadagno è un effetto scala, non informazione) e la mediana.
6. **Holm** sui 4 p del placebo, α 0,05 (il più piccolo deve essere ≤ 0,0125).
7. **Non concentrato** (lezione 123): riportando a R 0,25 l'operazione la cui riduzione aiuta di più, l'insieme resta sopra
   W3.2 in CAGR/DD.
Informativi (non decisivi): 2021–23 / 2024→, senza l'operazione migliore e senza le due migliori, WR, numero di operazioni,
perdita allo stop, buy & hold, rendimento totale e MAR come richiesto dal metodo.
Caso finto dei criteri (lezione 101, serie sintetica in conteggi_output.txt): "dimezzare tutto" può migliorare il CAGR/DD e
riduce sempre il DD, ma è bloccato dal criterio 3 in 3 casi su 3; il criterio 5 confronta con riduzioni di pari numero.

## 6. Scelta finale
Fra le varianti che passano 1–7, quella con il CAGR/DD insieme più alto; a parità (entro il 2%) quella che tocca meno operazioni.
Nessuna passa → W3.2 invariata. Anche se una passa, la proposta va all'utente con revisione critica prima di qualsiasi
modifica (CLAUDE.md: le correzioni che cambiano decisioni di W3 si presentano prima).

## 7. Limiti dichiarati prima
- **Pochi trade**: 9 long BTC e 10 long ETH dal 2021; le varianti toccano 0–7 operazioni per asset. Ogni esito è fragile.
- **D4 senza potenza**: su BTC dal 2021 non tocca nulla; sull'insieme sceglie 2 short ETH su 5 → solo 10 combinazioni distinte
  nel placebo, p minimo 0,1: **non può passare Holm per costruzione**. Resta in tabella come descrittiva.
- **D3**: 36 × 120 = 4.320 combinazioni distinte, meno delle 5.000 prove (estrazione con ripetizione, p minimo ~1/4.320).
- **Buchi**: D1 cieca prima del 07/2020 (BTC 2018–20 neutro) e solo funding fino al 06/2022. Il caso BTC 2018 non è
  verificabile da nessuna variante.
- **Soglie viste prima**: D2 e D4 nascono dall'analisi delle perdite già fatta (IS descrittivo); la correzione del funding
  neutro è stata fatta dopo i conteggi (§3). OOS 2023→ è vero fuori campione solo per D1 e solo in parte (le perdite 2024–26
  erano già note): il placebo e i vicini sono i controlli principali.
- **Effetto scala**: ridurre più operazioni abbassa il DD meccanicamente; per questo valgono i criteri 3 e 5.

## 8. File
`regole.py` (segnali e motore; verifica `python -I research/dimensione/regole.py`), `conteggi.py` → `conteggi_output.txt`,
`conteggi.csv`. Fase 2 (dopo il commit di questo PREREG): `fase2.py`, `README.md`.
