# Preregistrazione · Supertrend di TradingView (ATR 10, fattore 3) su BTC a 4h, 1D, 1W: da solo e dentro W3.2 · 23/11/2026

Scritta PRIMA di qualsiasi rendimento (di strategia o dopo un cambio di direzione). Finora eseguito solo `st_lib.py`: replica
dell'indicatore e controlli di proprietà (nessun rendimento calcolato). Va committata da sola. Definizioni, soglie e criteri non
si cambiano dopo; ogni idea nata dai risultati va in una nuova preregistrazione.

## 1. Domanda e cosa è già noto
L'utente chiede l'analisi dell'indicatore "Supertrend" di TradingView (Pine v6, `ta.supertrend(factor = 3, atrPeriod = 10)`,
direzione < 0 = rialzo con linea verde sotto il prezzo, > 0 = ribasso; avvisi al cambio di direzione).
Già noto, non si ripete: SuperTrend 1D come peso della size sulla vecchia v2 = nessun vantaggio (lezione 26, p 0,48); trailing a
k ATR settimanali dentro W3.x con k 2,0–3,0: 2,5 resta il migliore (lezioni 60, 105); TP e trailing stretto peggiorano (109);
medie su 4h/1D/1W: nessuna regola regge, uscite a 4h peggiori, short in perdita (117). Attesa dichiarata: il Supertrend è un
trailing ATR con inversione, quindi ci si aspetta lo stesso esito delle medie lente (long/flat ≈ buy & hold con meno drawdown;
short, inversione e 4h negativi; dentro W3.2 nessun miglioramento). Novità: la replica esatta dell'indicatore, i tre intervalli,
l'inversione long/short, il multi-intervallo e l'uso al posto del trailing di W3.2.

## 2. Indicatore e dati
- Replica (`st_lib.supertrend`): TR = max(H−L, |H−C₋₁|, |L−C₋₁|); ATR = RMA di Wilder su n barre con seme = media semplice delle
  prime n TR; bande di base hl2 ± fattore·ATR; banda inferiore finale = quella di base se è più alta della precedente o se la
  chiusura precedente era sotto la banda precedente, altrimenti la precedente (specchio per la superiore); direzione: dalla
  banda superiore si passa al rialzo (−1) se la chiusura supera la banda superiore, dalla inferiore al ribasso (+1) se la chiusura
  scende sotto la banda inferiore; linea = banda inferiore in rialzo, superiore in ribasso. Seconda implementazione indipendente
  (`supertrend_alt`) identica su 4h/1D/1W × 16 combinazioni; proprietà verificate (linea che non arretra, chiusura dal lato
  giusto, cambio solo in chiusura oltre la banda; unica eccezione, propria del codice Pine: 2 barre di cambio su 8.362 a 4h in
  cui una banda "vecchia" resta dal lato sbagliato per una candela con ombra enorme). Non è possibile un confronto dal vivo con
  TradingView: dichiarato.
- Dati: BTCUSDT spot Binance 4h (research/ema_sma/data, 2017-08-17 → 2026-11-22). 1D = 6 barre 4h (UTC); 1W = lunedì–domenica
  (W-SUN), solo barre chiuse. Per 1D e 1W la storia parte dal 2014 (f_long) così che l'indicatore sia a regime nel 2018. Misurato:
  la storia dal 2014 e quella solo Binance (dal 17/08/2017) danno lo stesso Supertrend 1D dal 10/10/2017 e lo stesso 1W dal
  13/01/2019; nel 2018 il settimanale dipende quindi da dove comincia il grafico: si riporta anche il 2018–20 con la storia corta.
- Parametri PRIMARI: ATR 10, fattore 3 (predefiniti), fissi, uguali su tutti gli intervalli e gli asset. Nessuna scelta sui dati.
- Periodi: 2018-01-01 → 2020-12-31; 2021-01-01 → 2023-12-31; 2024-01-01 → 2026-11-15 (dati congelati di W3.2). Il descrittivo e
  lo stato attuale arrivano al 22/11/2026.

## 3. Descrittivo (4h, 1D, 1W; 10/3; per periodo)
Cambi di direzione l'anno (al rialzo e al ribasso); durata dei trend (media, mediana, in barre e giorni); cambi "falsi" = direzione
invertita di nuovo entro 3 e entro 10 barre; quota di tempo in rialzo/ribasso; rendimento dalla chiusura della barra del cambio a
1, 3, 7, 14, 30 giorni e suo eccesso sulla media incondizionata dello stesso periodo (tutte le chiusure 4h come partenza);
rendimento medio a 7 e 30 giorni condizionato allo stato (rialzo/ribasso). Placebo: 1.000 traslazioni circolari delle date dei cambi
dentro ciascun periodo; p a due code sull'eccesso a 7 e 30 giorni sull'intero 2018–26; 12 test (3 intervalli × 2 versi × 2
orizzonti), soglia di Bonferroni 0,0042. Stato attuale al 22/11 sui tre intervalli (direzione, linea, distanza dal prezzo, data
dell'ultimo cambio) e accordo con W3.2 (short BTC dal 16/11).

## 4. Come strategia a sé (11 oggetti giudicati, tutti con 10/3)
Posizione = stato, letto alla chiusura della barra e eseguito all'apertura della barra 4h successiva (per 1D e 1W: chiusura della
candela 4h delle 20:00 del giorno / della domenica → apertura delle 00:00). Dal primo giorno si sta nello stato in corso.
- **S1** inversione: long se direzione −1, short se +1 (sempre a mercato). **S2** solo long: long se −1, altrimenti fuori.
  **S3** solo short: short se +1, altrimenti fuori. Ciascuna su 4h, 1D, 1W (9 oggetti).
- **S4a** multi-intervallo 1W + 1D: long se 1W e 1D sono entrambi al rialzo, short se entrambi al ribasso, altrimenti fuori.
  **S4b** lo stesso con 1D come regime e 4h come innesco. (Lati long e short di S4 riportati separati, come descrizione.)
Costi (come W3.2 e lo studio 117): long spot 0,1% + 0,1% di slippage per lato; short perp 0,05% + 0,1% per lato e funding reale
giornaliero (f_long, dal 2020; prima zero: favorisce gli short nel 2018–19), prezzo spot anche per lo short. 10.000 $, 1x, tutto
il capitale, short a quantità fissa. Simulazione continua dal 2018-01-01; i periodi sono fette della stessa curva; un trade
appartiene al periodo d'ingresso. Metriche: capitale da 10.000 $, CAGR, max drawdown sulle chiusure giornaliere, S = CAGR/|DD|,
trade, win rate, capitale senza i 2 trade migliori. Buy & hold comprato all'apertura del primo giorno del periodo, stessi costi.
**Versione con tetto di rischio** (confronto alla pari con W3.2, riportata accanto; non è una seconda possibilità): esposizione =
min(1; 0,25 / (2,5·ATR settimanale 14 / chiusura)) all'ingresso e stop di protezione a 2,5 ATR settimanali dalla chiusura del
segnale, toccato dentro la barra → uscita a min(apertura, stop); dopo lo stop si resta fuori fino al cambio di stato successivo.
**Valida** solo se, in TUTTI e tre i periodi: CAGR > 0; S > S del buy & hold; DD ≥ −35%; CAGR ancora > 0 togliendo i 2 trade
migliori del periodo; e in più placebo p ≤ 0,0045 (0,05 / 11 oggetti). Placebo del criterio (P1, cambi sfasati): la serie delle
posizioni traslata circolarmente di un numero casuale di barre (fra 30 giorni e durata − 30 giorni) sull'intero 2018–26, 1.000
volte; p = quota con S (intero 2018–26) ≥ reale. Placebo descrittivo (P2, prezzi rimescolati a blocchi di 20 giorni, 300 serie,
indicatore ricalcolato): dice se il risultato viene da tendenze più lunghe di 20 giorni.
**Mappa dei parametri** (solo descrizione, non per scegliere): ATR 7/10/14/21 × fattore 2/2,5/3/4 = 16 combinazioni per ciascuno
degli 11 oggetti. "10/3 in zona stabile" se almeno 6 degli 8 vicini in griglia hanno lo stesso segno di (S − S buy & hold)
sull'intero 2018–26 e il valore di 10/3 sta fra il minimo e il massimo dei vicini. Si riporta anche quante delle 16 combinazioni
superano i criteri dei tre periodi (senza placebo).
**Confronto con W3.2** (radar/weekly.py non modificato; 2021–26 su f_repo, 2018–20 su f_long; ogni periodo da 10.000 $).
Dichiarato: W3.2 è stata costruita vedendo tutto il 2021–26; il Supertrend 10/3 è un valore predefinito non scelto sui dati.

## 5. Dentro W3.2 (4 varianti; copia di radar.weekly.simulate in research/, verificata al dollaro contro l'originale)
"Cambio contro" = cambio di direzione del Supertrend 10/3 contro la posizione avvenuto dopo l'ingresso (evento, non stato).
- **K1** Supertrend 1W al posto del trailing: lo stop iniziale a 2,5 ATR resta fisso (niente cricchetto); uscita al cambio 1W
  contro (chiusura della domenica → apertura del lunedì). Uscite EMA21 e distribuzione, ingressi ed esposizione invariati.
- **K2** uscita anticipata: tutto come W3.2, più uscita all'apertura del giorno dopo un cambio 1D contro. Rientro alla prima
  decisione domenicale con segnale W3.2 valido (senza filtro).
- **K3** filtro d'ingresso: al segnale domenicale si entra il lunedì solo se il Supertrend 1D è concorde; altrimenti si entra
  all'apertura del giorno dopo la prima chiusura giornaliera concorde (da lunedì a sabato; esposizione e stop del segnale; segnale
  annullato se una chiusura giornaliera supera lo stop iniziale). Alla domenica successiva (scadenza, N = 7 giorni) decide di
  nuovo W3.2: se il segnale è ancora valido si entra comunque. Uscite di W3.2.
- **K4** come K2 ma con il cambio 4h contro, eseguito all'apertura della candela 4h successiva (stop controllato sulle candele
  4h precedenti dello stesso giorno). Attesa dichiarata: peggiore.
Una variante **migliora** solo se: S > S di W3.2 sia nel 2021–23 sia nel 2024–26; S nel 2018–20 non inferiore a W3.2; DD
2021–26 ≥ −30%; win rate 2021–26 ≥ 70%; placebo p ≤ 0,0125 (0,05 / 4): 500 traslazioni circolari della serie dei cambi (K1, K2,
K4) o dello stato (K3), p = quota con capitale 2021–26 ≥ reale. Si elencano i trade che cambiano rispetto a W3.2 (dipendenza
da ≤ 2 trade = non dimostrato).

## 6. Conferma esterna su ETH (senza ottimizzare)
Dati research/w32_multi (ETH spot giornaliero dal 17/08/2017; funding data/eth_funding.csv dal 2020): S1–S3 su 1D e 1W e S4a,
stessi parametri, costi, periodi e criteri (senza placebo). Non esistono nel repo candele 4h di ETH: S 4h e S4b non si
confermano su ETH (dichiarato; la storia corta rende il settimanale ETH del 2018 non a regime). K1–K3 su W3.2 ETH (dati
research/top10_w3, 2021 → 10/11/2026) contro W3.2 ETH: una variante che migliora BTC conta solo se non peggiora S su ETH.

## 7. Cosa NON si fa
Nessuna modifica a radar/, tests/ o al tool. Nessuna ricerca dei parametri che salvano il risultato: 10/3 si giudica com'è; la
griglia è una mappa. Se una variante supera i criteri si segnala soltanto. Deviazioni dal metodo abituale richieste
dall'incarico: 11 + 4 oggetti (oltre le 8 varianti), commit di questa preregistrazione.
