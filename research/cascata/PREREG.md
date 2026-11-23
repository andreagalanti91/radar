# Preregistrazione · Uscita di profitto nel giorno di "cascata a favore" e rientro su W3.2 (BTC settimanale) · 23/11/2026

Scritta PRIMA di qualsiasi rendimento. Finora è stato eseguito solo `cs_count.py` (numero di giorni-evento e grandezze del
giorno stesso; nessun rendimento successivo, nessuna simulazione di varianti): risultato in `conteggi.txt`. Va committata da sola.
Regole, soglie, vicini e criteri non si cambiano dopo; ogni idea nata dai risultati va in una nuova preregistrazione.

## 1. Domanda dell'utente
W3.2 è short da 65.286 $ (16/11/2026). Il 21/11 BTC è sceso a 55.130 $ ed è rimbalzato a 61.000 $. "Non sarebbe stato meglio
chiudere a 55 visto che c'è stata una cascata di mercato? Non è meglio analizzare giorno per giorno e prendere la decisione
intraday anche su posizioni weekly?"
Già escluso (non si ripete): TP fissi in % con rientro e trailing stretto (lezione 109, 0/8); uscite giornaliere su livelli e
flusso spot/perp (114, 0/8); uscite a scaglioni, stop, DCA (105); fasce di liquidazione e squeeze (92, 93); "crollo da volume"
come uscita CONTRO la posizione long (69). Novità: uscita di PROFITTO nel giorno di movimento violento A FAVORE della posizione
con volume anomalo, con rientro esplicito; test evento sul rimbalzo dopo una cascata.

## 2. Riferimento, dati, costi
- W3.2 = radar/weekly.py: rischio allo stop iniziale 25%, stop e trailing 2,5 ATRw a cricchetto, uscite settimanali EMA21 e
  distribuzione; long spot, short perp; spot 0,1%/lato, perp 0,05%/lato + funding reale, slippage 0,1%. 10.000 $, 1x.
- BTC: dati congelati research/p2_nuovi (f_repo) 2021-01-01 → 2026-11-15; IS 2021–23 e OOS 2024–26 ripartono da 10.000 $.
  2018–20: f_long (proxy) con volume SOLO spot Binance (i perp non esistono): dichiarato. ETH (conferma esterna, stessi
  parametri, nessuna ottimizzazione): radar.data.load_asset("ETH") fino al 15/11, dal 2021.
- Il caso del 21/11 è FUORI dal campione del test (dati del test fino al 15/11): si descrive con i dati del tool.

## 3. Definizioni (grandezze note alla chiusura del giorno t; lato s della posizione)
atr1 = ATR14 giornaliero (Wilder) alla chiusura di t−1. V = spot_vol + perp_vol (Binance). vr = V_t / media di V nei 30 giorni
precedenti. rA = s·(C_t − C_{t−1})/atr1. eA = s·(E_t − C_{t−1})/atr1 con E = massimo (long) o minimo (short).
tail = s·(E_t − C_t)/(H_t − L_t) = quota dell'intervallo del giorno restituita in chiusura.
- **D1 "cascata in chiusura"** (soglie dell'incarico): rA ≥ 2 e vr ≥ 2.
- **D3 "cascata con rifiuto"**: eA ≥ 1,25 e vr ≥ 2 e tail ≥ 0,5. Soglie scelte guardando le grandezze del 21/11/2026
  (eA 1,36, vr 2,19, tail 0,87; rA −0,45: il giorno ha chiuso in rialzo, quindi D1 NON lo riconosce; nemmeno il 20/11:
  rA 1,15). È la definizione "su misura" del caso dell'utente, la più favorevole alla sua ipotesi; il 21/11 non è nel campione.
- **LIM "ordine a limite"**: ordine di chiusura piazzato prima dell'apertura a C_{t−1} + s·2·atr1 (2 ATR giornalieri a favore
  dalla chiusura precedente), rinnovato ogni giorno; nessuna condizione di volume (non è nota prima).
Conteggi (giorni a favore dentro i trade W3.2 / trade toccati; `conteggi.txt`): BTC 2021+ D1 14/9 (IS 6, OOS 8), D3 9/5 (6/3),
LIM 36/12; BTC 2018–20 D1 7/4, D3 2/2, LIM 17/5; ETH D1 6/4, D3 3/2, LIM 24/12. In tutto il campione BTC 2021+ (anche fuori
dai trade): D1 14 giorni al ribasso e 15 al rialzo; D3 12 e 10.

## 4. Esecuzione e rientri (motore `cs_engine.py`, copia di tp_engine/radar.weekly)
- Decisione alla chiusura del giorno di cascata, uscita all'APERTURA successiva (slippage 0,1% + commissione). Mai al minimo.
  Se nello stesso giorno scatta lo stop/trailing vale lo stop. Se la domenica W3.2 decide l'uscita, vale quella.
- LIM: riempito al livello (o all'apertura se apre oltre), con slippage 0,1% e commissione (prudente); stop nello stesso giorno
  → vale lo stop.
- "Tutto": chiude tutta la posizione. "Metà": chiude il 50% una sola volta per trade; il resto segue W3.2, nessun rientro.
- **R1**: dopo l'uscita si è flat e vale W3.2: si rientra alla prima decisione domenicale SUCCESSIVA in cui il segnale
  d'ingresso W3.2 è vero (lunedì all'apertura), con dimensione W3.2 (rischio 25% allo stop 2,5 ATRw dalla chiusura del segnale).
- **R2** (X = 5%, fissato ora): come R1, più rientro nello stesso lato all'apertura successiva al primo giorno in cui la
  chiusura giornaliera è rimbalzata di almeno il 5% contro la posizione rispetto al prezzo d'uscita (short: C ≥ uscita × 1,05;
  long: C ≤ uscita × 0,95) e il regime di quel lato è valido sull'ultima settimana chiusa (long: C > SMA40 e EMA20 in
  salita; short: C < SMA40, SMA40 in calo su 4 settimane, EMA20 in calo). Dimensione: rischio 25% allo stop a 2,5 ATRw
  (ultimo ATR settimanale) dalla chiusura di quel giorno. La possibilità decade al primo rientro o a regime finito (domenica).
- **R3**: nessun rientro: nuovi ingressi solo dopo la data in cui il trade originale di W3.2 è uscito.
- Dopo un rientro (R1/R2) una nuova cascata può far uscire di nuovo.

## 5. Varianti (6)
| Id | Evento | Quota | Rientro | Vicini (descrittivi) |
|---|---|---|---|---|
| C1 (primaria) | D1 | tutto | R1 | rA 1,5 / 2,5; vr 1,5 / 2,5; rP ≥ 7% al posto di rA |
| C2 | D1 | tutto | R2 (5%) | X 3% / 8% |
| C3 | D1 | tutto | R3 | — |
| C4 | D1 | metà | — | — |
| C5 | D3 | tutto | R1 | eA 1 / 1,5 / 2; tail 1/3; vr 1,5 |
| C6 | LIM 2 ATR | tutto | R1 | k 1,25 / 1,5 / 2,5 |

## 6. Metriche
Finale, CAGR, max DD giornaliero, CAGR/DD, trade (con i rientri), win rate, peggiore, numero di uscite-cascata; per 2021+,
IS 2021–23, OOS 2024–26, 2018–20; buy & hold. Trade aperto a fine dati chiuso all'ultima chiusura.

## 7. Criteri (tutti, per ciascuna variante)
1. CAGR/DD migliore di W3.2 sia in IS 2021–23 sia in OOS 2024–26.
2. 2018–20: CAGR/DD non peggiore di W3.2.
3. DD 2021+ entro −30%.
4. Win rate 2021+ ≥ 70%.
5. Non dipende da ≤ 2 trade: somma dei Δ log-rendimento per trade W3.2 (variante − W3.2; i rientri si sommano al trade
   d'origine, come in tp_rientro) ancora > 0 togliendo i 2 Δ più favorevoli.
6. Permutazione esatta dei segni sui Δ per trade non nulli: p ≤ soglia di Holm su 6 test (α 0,05).
7. Placebo: 500 ripetizioni (seme 20261123) in cui ogni uscita-cascata osservata nel trade W3.2 è sostituita da un'uscita
   (stessa quota, stesso rientro, apertura successiva) in un giorno a caso DELLO STESSO trade W3.2, non di cascata, con
   guadagno aperto in chiusura entro ±5 punti percentuali da quello del giorno di cascata (se nessun giorno è nella banda: i 5
   giorni col guadagno più vicino). p = quota delle ripetizioni con CAGR/DD 2021+ ≥ variante; serve p < 0,05.
8. Conferma esterna: su ETH 2021+ CAGR/DD ≥ W3.2 su ETH (stessi parametri).
**Potenza dichiarata: bassa.** 13 trade, 5–12 trade toccati dall'evento: con ≤ 6 Δ non nulli la permutazione non può scendere
sotto 1/64 = 0,016 > soglia di Holm 0,0083; servono ≥ 7 Δ tutti positivi. Un esito negativo vale "nessun miglioramento
dimostrabile". Una variante che passa NON entra in radar/: si segnala all'utente.

## 8. Parte descrittiva (nessun criterio)
1. Dentro i trade W3.2 (2021+ e 2018–20), per D1 e D3: numero di cascate a favore; movimento del prezzo nel verso del trade a
   3, 7, 14 giorni dall'apertura successiva (prosecuzione > 0, rimbalzo < 0); in quanti casi il trade ha poi segnato, prima
   dell'uscita di W3.2, un estremo migliore (intragiornaliero e in chiusura) di quello del giorno di cascata; uscita di W3.2
   contro l'apertura successiva alla cascata.
2. Caso 21/11/2026: quali definizioni lo riconoscono; prezzo d'uscita eseguibile (apertura del 22/11; limite a k ATR);
   rientro secondo R1/R2; confronto in dollari (posizione W3.2 su 10.000 $ e su 50.000 $) con il tenere, all'ultimo prezzo
   disponibile.
3. Test evento generale (anche fuori dai trade): dopo una cascata al RIBASSO (D1 e D3 lato short, primo giorno, pausa 7
   giorni) BTC rimbalza? Rendimento dall'apertura successiva alla chiusura a 3, 7, 14 giorni meno la media di tutti i giorni;
   orizzonte primario 7 giorni; placebo: 10.000 estrazioni di n giorni a caso (stessa pausa), p a due code; due metà
   (2021–23 / 2024–26); 2018–20 ed ETH come conferma; speculare al rialzo come controllo; Holm sui 2 test primari (D1, D3 a 7 g).
