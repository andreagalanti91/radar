# Multi-asset · W3.1 "solo prezzo" ed EMA200D + VIX — RISULTATI (fase 2, 22/11/2026)

PREREG: `PREREG.md` (commit 13b0e82, committato da solo prima di ogni backtest). Codice: `ma_lib.py` (regole), `run.py`
(esecuzione). Uscite: `risultati.txt` (tutto), `principali.csv`, `periodi.csv`, `robustezza.csv`, `placebo.csv`, `decenni.csv`,
`dow.csv`, `btc.csv`, `panic.csv`. Controllo del motore: `ma_lib.s1_sim` con i segnali di W3.1 su BTC riproduce gli stessi 13 trade
di `radar.weekly` (date e motivi identici). W3.1 dal 2021 riprodotta: 27.190 $.

## Verdetto
- **W3.1 è generale? NO.** S1 long/short (W3.1 senza flusso perp) "funziona" su 0 asset su 13 (ne servivano 7); batte il buy & hold
  in CAGR/DD sul periodo intero solo su BTC. Sulle azioni a rischio 10% fa DD −42/−78% con WR 28–48%: troppi stop piccoli, e i
  trend lunghi delle azioni vincenti li prende meglio il buy & hold. Controllo Dow 2000: passa il criterio dei periodi 2/24.
- **EMA200D + VIX funziona? NO, secondo i criteri.** Nessun placebo sotto la soglia corretta (p < 0,00012). Il caso migliore è
  l'**S&P 500**: S3 dal 1991 ha CAGR 9,1% con DD −39,5% (buy & hold 8,9%, −56,8%), vince 2 sottoperiodi su 3 e regge tutti i
  controlli di robustezza, ma il placebo dà p = 0,009 e dal 2021 perde (CAGR/DD 0,34 contro 0,44). S2 sull'S&P dal 1928 ha p = 0,00025,
  vicino alla soglia ma sopra. Su META S3 regge tutto tranne il placebo (p = 0,0065, 42 trade). Sulle altre azioni e sui metalli il
  vantaggio è nullo o negativo; sul Dow 2000 S3 passa i periodi su 9/24 (38%).
- **BTC**: nessuna regola solo-prezzo si avvicina a W3.1 (CAGR/DD 1,90). S1 0,68; S2 0,26; S3 con VIX 0,23 (DD −71%); S3 con DVOL 0,00.
  Su BTC "battere il buy & hold in 2 sottoperiodi su 3" è facile: il buy & hold perde nel 2021–22 e nel 2025–26.
- **W3.1 + panic**: 4 ingressi con il VIX, 3 con il DVOL: non valutabili (meno di 5 eventi, come fissato nel PREREG). In descrittivo
  il VIX aggiunge 1.600 $ ma porta il DD da −9,8% a −14,7%; con il DVOL si perde (22,9k); nel 2018–20 peggiora (14,5k contro 16,7k, DD −30%).
- **V8 (W3.1 filtrata da EMA200D)**: dal 2021 non blocca nessun ingresso (0 eventi): non eseguita.

## Periodo intero, 10.000 $ (CAGR %, DD giornaliero %, CAGR/DD)
| Asset (da) | Buy & hold | S1 long/short | S1 solo long | S2 EMA200D | S3 EMA200D+VIX (dal 1991) |
|---|---|---|---|---|---|
| S&P 500 (1928) | 2,84M · 5,9 · −86 · 0,07 | 131k · 2,7 · −58 · 0,05 | 308k · 3,6 · −42 · 0,08 | 3,46M · 6,2 · −45 · **0,14** | 229k · 9,1 · −40 · **0,23** (B&H 0,16) |
| GLD (2005) | 66,6k · 9,5 · −46 · 0,21 | 18,5k · 3,0 · −59 · 0,05 | 26,7k · 4,8 · −41 · 0,12 | 47,1k · 7,7 · −28 · 0,27 | 48,7k · 7,8 · −30 · 0,27 |
| SLV (2007) | 27,7k · 5,4 · −76 · 0,07 | 14,9k · 2,1 · −71 · 0,03 | 26,4k · 5,1 · −47 · 0,11 | 29,0k · 5,6 · −65 · 0,09 | 26,1k · 5,0 · −62 · 0,08 |
| NVDA (2000) | 15,4M · 31,5 · −90 · 0,35 | 309k · 13,7 · −42 · 0,32 | 484k · 15,6 · −33 · 0,47 | 3,68M · 24,6 · −64 · 0,39 | 3,01M · 23,7 · −70 · 0,34 |
| AAPL (1981) | 55,4M · 21,2 · −82 · 0,26 | 348k · 8,2 · −60 · 0,14 | 901k · 10,5 · −40 · 0,26 | 14,4M · 17,6 · −82 · 0,21 | 2,91M · 17,1 · −84 · 0,21 |
| MSFT (1987) | 27,8M · 22,1 · −69 · 0,32 | 35,2k · 3,2 · −67 · 0,05 | 113k · 6,3 · −45 · 0,14 | 1,73M · 13,9 · −64 · 0,22 | 3,31M · 17,6 · −52 · 0,34 |
| GOOGL (2005) | 382k · 18,7 · −65 · 0,29 | 34,0k · 5,9 · −44 · 0,13 | 55,5k · 8,4 · −27 · 0,32 | 137k · 13,1 · −35 · 0,37 | 132k · 12,9 · −51 · 0,25 |
| AMZN (1998) | 6,61M · 25,6 · −94 · 0,27 | 47,1k · 5,6 · −50 · 0,11 | 120k · 9,1 · −36 · 0,26 | 148k · 9,9 · −69 · 0,14 | 1,18M · 18,2 · −79 · 0,23 |
| META (2013) | 220k · 25,7 · −77 · 0,34 | 28,9k · 8,2 · −43 · 0,19 | 33,9k · 9,5 · −26 · 0,36 | 163k · 23,0 · −40 · 0,58 | 274k · 27,8 · −38 · **0,72** |
| AVGO (2010) | 1,92M · 38,1 · −48 · 0,79 | 17,0k · 3,3 · −57 · 0,06 | 27,4k · 6,4 · −41 · 0,16 | 290k · 23,0 · −50 · 0,46 | 858k · 31,4 · −62 · 0,51 |
| TSLA (2011) | 1,83M · 40,3 · −74 · 0,55 | 27,4k · 6,8 · −56 · 0,12 | 44,0k · 10,1 · −47 · 0,22 | 104k · 16,4 · −67 · 0,24 | 191k · 21,1 · −67 · 0,31 |
| BRK-B (1997) | 217k · 11,0 · −54 · 0,20 | 8,1k · −0,7 · −65 · −0,01 | 24,7k · 3,1 · −48 · 0,07 | 33,5k · 4,2 · −43 · 0,10 | 82,3k · 7,4 · −47 · 0,16 |
| LLY (1973) | 11,5M · 14,1 · −68 · 0,21 | 20,1k · 1,3 · −78 · 0,02 | 151k · 5,2 · −57 · 0,09 | 1,05M · 9,1 · −67 · 0,14 | 417k · 11,0 · −63 · 0,17 |

Per S3 il buy & hold confrontato parte dal 1991: è uguale a quello della colonna solo per gli asset nati dopo il 1991.
S&P 500 con dividendi (`^SP500TR`) dal 1991: 427k, CAGR 11,0%, DD −55%, CAGR/DD 0,20 (ancora sotto S3, che però non incassa i dividendi).

## Dal 2021 (10.000 $ → capitale finale, CAGR/DD)
| Asset | B&H | S1 L/S | S1 long | S2 | S3 |
|---|---|---|---|---|---|
| S&P 500 | 18,7k · 0,44 | 13,7k · 0,25 | 15,3k · 0,42 | 13,1k · 0,21 | 17,2k · 0,34 |
| GLD / SLV | 17,7k · 0,29 / 14,6k · 0,10 | 16,2k · 0,27 / 16,4k · 0,18 | 18,8k · 0,60 / 22,8k · 0,68 | 19,2k · 0,52 / 16,0k · 0,15 | 17,9k · 0,46 / 13,4k · 0,09 |
| NVDA / AAPL / MSFT | 96,2k · 0,71 / 27,3k · 0,56 / 23,4k · 0,42 | 26,1k / 10,8k / 9,3k | 28,5k / 13,3k / 11,3k | 117,5k · 1,12 / 17,0k / 12,3k | 128,5k · 0,97 / 18,9k / 18,7k |
| GOOGL / AMZN / META | 31,0k · 0,48 / 15,5k · 0,14 / 21,1k · 0,18 | 15,5k / 5,7k / 13,7k | 16,1k / 8,1k / 15,5k | 22,9k / 13,2k / 25,2k · 0,43 | 37,8k · 0,82 / 14,8k · 0,19 / 29,0k · 0,52 |
| AVGO / TSLA / BRK-B / LLY | 80,0k / 14,2k / 25,0k / 86,3k | 19,8k / 7,5k / 11,1k / 21,1k | 19,4k / 8,9k / 14,6k / 23,7k | 38,4k / 6,6k / 13,1k / 36,7k | 75,9k / 6,3k / 19,3k / 48,4k |

## BTC dal 2021 (10.000 $; sottoperiodi 2021–22 / 2023–24 / 2025–26)
| Regola | Capitale | CAGR | DD | CAGR/DD | Trade | WR |
|---|---|---|---|---|---|---|
| Buy & hold | 22.280 | 14,6% | −76,6% | 0,19 | – | – |
| **W3.1** | **27.190** | 18,6% | −9,8% | **1,90** | 13 | 92% |
| S1 long/short (senza flusso) | 20.074 | 12,6% | −18,5% | 0,68 | 15 | 87% |
| S1 solo long | 16.867 | 9,3% | −18,5% | 0,50 | 12 | 75% |
| S2 EMA200D | 19.844 | 12,4% | −47,4% | 0,26 | 35 | 26% |
| S3 VIX 34 | 24.392 | 16,4% | −71,3% | 0,23 | 30 | 33% |
| S3 DVOL 93,9 | 10.173 | 0,3% | −71,4% | 0,00 | 38 | 26% |
| W3.1 + panic VIX | 28.810 | 19,8% | −14,7% | 1,34 | 13 + 4 | – |
| W3.1 + panic DVOL | 22.918 | 15,2% | −15,7% | 0,96 | 13 + 3 | – |

Trade panic (esposizione di W3.1, rischio 10%): VIX 27/01/21 +9,0% (2,6% della quota), 09/05/22 −28,2% (−6,6%), 05/08/24 +17,7%
(+6,1%), 04/04/25 +11,8% (+3,9%); DVOL 24/04/21 −32,7% (−10,0%), 28/07/21 −0,4%, 11/05/22 −28,3% (−6,6%). Nel 2018–20 con il VIX: 05/02/18
−4,9%, 27/02/20 −39,2% (−14,8% della quota), 30/04/20 +3,2%.

## Robustezza (dettagli in robustezza.csv, placebo.csv)
- Placebo (stessi trade in date casuali, stessa esposizione): migliori p sono SPX S2 0,00025, NVDA S1 long 0,0023, BTC S1 0,0032,
  META S3 0,0065, SPX S3 0,009; tutti sopra la soglia corretta 0,00012. Senza correzione per test multipli sarebbero
  significativi, ma su 415 configurazioni ci si aspettano ~4 p < 0,01 per puro caso.
- Superano tutti i controlli contro il buy & hold (vicini, apertura del giorno dopo, costi doppi, senza il trade migliore) solo
  SPX S2, SPX S3, META S3 e BTC S1 (L/S e long). Su BTC S2/S3, senza il trade migliore il CAGR/DD va sotto il buy & hold.
- Bias di selezione: sulle 10 azioni scelte ex post il buy & hold è eccezionale (CAGR 11–40%); nessuna regola lo batte con
  continuità. Il controllo Dow 2000 conferma: S1 L/S 2/24, S1 long 7/24, S2 7/24, S3 9/24 passano il criterio dei periodi (le 10
  azioni scelte: 0, 2, 3, 2 su 10). CAGR/DD mediano sul Dow: S3 0,13, S2 0,11, buy & hold 0,17.
- S&P 500 per decennio (decenni.csv, CAGR/DD): S2 batte il buy & hold in 8 decenni su 10 (dagli anni '30 ai 2000) e perde nei
  2010 (0,41 contro 0,56) e nei 2020 (0,32 contro 0,34). S3 batte negli anni '90, nei 2000 e nei 2020 (0,41 contro 0,34) e pareggia
  nei 2010. S1 batte solo negli anni '30, '70 e 2000. È il risultato più coerente della ricerca, ma resta sopra la soglia corretta.

## Deviazioni dal PREREG
1. Placebo: le estrazioni si fermano a 2.000 quando p > 0,01 (non può più scendere sotto 0,00012); le altre arrivano a 20.000.
   Il verdetto non cambia.
2. V6/V7: applicato il testo del PREREG (ogni incrocio della soglia con W3.1 flat), non il contatore della fase 1, che teneva conto
   anche dello stato interno di S3. VIX: 4 eventi come in fase 1; DVOL: 3 invece di 2 (si aggiunge il 28/07/2021). Sempre < 5:
   non valutabili.
3. Placebo su BTC S1: rappresentazione chiusura→chiusura senza funding (approssimazione; la statistica reale è ricalcolata allo stesso modo).
4. Costi doppi su BTC: commissioni e slippage di W3.1 ×2 (S1) o 0,4% per lato (S2/S3), invece di "0,15%", che vale per le azioni.
5. FRED non raggiungibile: VIX controllato con Yahoo invece di FRED (già dichiarato nel PREREG).

## Lezione proposta (104)
**Lezione 104**: W3.1 senza flusso perp non è una regola generale: su S&P 500, oro, argento, 10 grandi azioni e 24 titoli del Dow 2000
non batte il buy & hold in CAGR/DD (0/13 asset, 2/24 nel controllo). Anche su BTC, senza flusso il CAGR/DD scende da 1,90 a 0,68:
il vantaggio di W3.1 viene dal flusso perp e dalla volatilità di BTC, non dalle medie (conferma 74 e 87). L'indicatore EMA200D + VIX
è soprattutto un riduttore di drawdown sugli indici azionari: sull'S&P 500 dal 1991 fa lo stesso CAGR del buy & hold con DD −40%
invece di −57% e regge tutti i vicini, ma dopo la correzione per 415 test non si distingue dal caso, e dal 2021 perde. Su BTC
(VIX o DVOL) peggiora W3.1, e i rari ingressi "panic" (4 in 6 anni) non sono valutabili.
Uso possibile: l'S&P 500 con S3 come esempio per l'utente, non come segnale. Nessuna modifica a W3.1.
