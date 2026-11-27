# MACD settimanale su SOL come strategia a sé (solo long) · PREREGISTRAZIONE (27/11/2026)

Idea dell'utente: "Implementiamo il MACD. Buy → da −3 a −50. Sell → +10 in poi." Asset SOL, MACD settimanale 12/26/9,
strategia a sé, solo long. Valore e momento d'acquisto: "non so, proponi tu" → R2–R4 sono le proposte, R1 è la lettura letterale.
Fissato **prima di calcolare qualsiasi rendimento** (fase 1: solo dati e conteggi, `conteggi.py` / `CONTEGGI.md`).
Questo file va committato da solo prima di eseguire qualsiasi script con rendimenti (fase 2). W3.2 (`radar/weekly.py`) non si tocca.

## 1. Dati e indicatori
- Dati congelati: `research/w32_asset2/crypto/data/SOL_spot.csv.gz` (spot Binance giornaliero UTC, SOLBUSD fino al 11/08/2020 poi
  SOLUSDT; dal 10/04/2020 al 24/11/2026). Nessun nuovo scaricamento.
- Candele settimanali W-SUN come W3.2 (`weekly_bars`): open = open del lunedì, close = close della domenica UTC; si usano solo le
  settimane chiuse nei dati (prima 12/04/2020, parziale di 3 giorni come in W3.2; ultima chiusa 22/11/2026).
- MACD 12/26/9 sulla close settimanale: linea = EMA12 − EMA26 (`ewm(span, adjust=False)`, come W3.2), signal = EMA9 della linea,
  istogramma = linea − signal. Ogni valore usa solo close fino alla domenica di decisione (nessuno sguardo al futuro).
- Riscaldamento: segnali ammessi solo dalla 35ª candela (26 + 9) = domenica **06/12/2020**; prima esecuzione possibile lunedì
  07/12/2020. È il "primo segnale possibile" del periodo intero.
- Decisione alla close della domenica, esecuzione all'**open del lunedì** successivo (open giornaliero del lunedì).

## 2. Varianti (4 principali + 4 descrittive con stop = 8)
Stato flat/long, tutto dentro/tutto fuori. "Linea" = linea MACD alla close della domenica.
- **R1 (letterale)**: da flat compra se −50 ≤ linea ≤ −3; da long vende se linea ≥ +10.
- **R2 (ripartenza)**: da flat compra se c'è incrocio al rialzo (linea > signal questa settimana e linea ≤ signal la precedente) e
  nella settimana dell'incrocio −50 ≤ linea ≤ −3; vendita come R1.
- **R3 (istogramma)**: come R1 con le stesse soglie applicate all'istogramma: compra se −50 ≤ ist ≤ −3, vende se ist ≥ +10.
- **R4 (normalizzata)**: come R1 sulla linea normalizzata `linea_n = linea × P_IS / close`, cioè soglie in % del prezzo.
  P_IS = **mediana delle close settimanali dal 12/04/2020 al 25/12/2022 (142 settimane, periodo IS) = 32,11 $** (calcolata solo
  sui prezzi, prima di ogni rendimento; nessuna griglia). Soglie equivalenti in % del prezzo: compra se −155,7% ≤ linea/close ≤
  −9,34%, vende se linea/close ≥ +31,1%. (Il limite −155,7% non è mai vincolante: di fatto R4 compra sotto −9,34%.)
- **R1s, R2s, R3s, R4s (con stop, SOLO DESCRITTIVE, riferimento di rischio, non candidate)**: come sopra più stop a −20% dal prezzo
  d'ingresso, controllato sul minimo giornaliero; uscita a 0,80 × ingresso, o all'open se il giorno apre già sotto lo stop.
  Dopo uno stop si rientra con la stessa regola alla prima domenica di decisione successiva (regola di stato, nessun riarmo).
- Nessun'altra variante. Nessuna modifica di soglie dopo aver visto i risultati.

## 3. Esecuzione
10.000 $, 1x spot, tutto dentro/tutto fuori, costi 0,1% per lato + slittamento 0,1% per lato (0,2% per lato in totale);
liquidità a 0% quando flat. Equity giornaliera mark-to-market sulle close; DD massimo giornaliero. Posizione aperta all'ultimo dato
valutata alla close del 24/11/2026 (conta come trade aperto: non entra nel WR sulle chiuse).

## 4. Periodi e riferimenti
- **Intero**: dal 07/12/2020 (primo segnale possibile) al 24/11/2026. **IS**: fino al 31/12/2022; **OOS**: dal 01/01/2023;
  **dal 2024** a parte. Rendimento di sottoperiodo = variazione dell'equity della corsa intera fra inizio e fine del sottoperiodo
  (le posizioni aperte proseguono). In più, per la preferenza dell'utente, la corsa **dal 01/01/2021 con 10.000 $** partendo flat.
- Riferimenti (stesse date, stessi costi dove calcolati qui): buy & hold SOL; W3.2 su SOL 80.661 $ dal 11/01/2021
  (research/sol_ciclo, rischio 25%); W3.2 su BTC 84.820 $ dal 2021; MACD flip della lezione 79 ricostruito su SOL in versione solo
  long (compra all'incrocio al rialzo, vende all'incrocio al ribasso, stesse candele ed esecuzione di questo studio).
- Metriche: capitale finale, rendimento, CAGR, DD giornaliero, CAGR/DD, trade, WR sulle chiuse, esposizione, per anno.

## 5. Criteri (come sol_ciclo; tutti richiesti per "valida", solo sulle 4 principali)
1. CAGR/DD > CAGR/DD del buy & hold sullo stesso periodo intero.
2. DD giornaliero ≥ −35%.
3. WR sulle chiuse ≥ 60%.
4. Rendimento > 0 in IS, in OOS e dal 2024.
5. ≥ 8 trade (ingressi) nel periodo intero.
**Conferma** (richiesta anch'essa):
6. Senza il trade migliore (rendimento composto togliendolo) capitale finale > 10.000 $.
7. Vicini: 4 corse — banda d'acquisto ×0,5 ([−25, −1,5]) e ×2 ([−100, −6]) con vendita +10; vendita +5 e +20 con banda [−50, −3]
   (per R4 sulle soglie normalizzate, per R3 sull'istogramma) — CAGR/DD sopra il buy & hold in almeno 2 su 4.
8. Placebo: 2.000 prove (seme 7); in ogni prova lo stesso numero di trade con le stesse durate (in settimane), ingressi a lunedì
   casuali nel periodo intero, senza sovrapposizioni; p = quota di prove con capitale finale ≥ quello della variante;
   correzione di Holm su 4 varianti (R1–R4), α = 0,05.
Le varianti con stop si riportano solo come rischio (DD, perdita peggiore), senza verdetto.

## 6. Limiti dichiarati
- SOL ha poco storico (dal 04/2020; con il riscaldamento dal 12/2020): un solo grande ciclo completo rialzo/ribasso/rialzo,
  pochi trade attesi, potenza statistica bassa.
- Le soglie −3/−50/+10 sono dell'utente e potrebbero essere state scelte guardando il grafico recente (prezzi 80–250 $): rischio di
  adattamento ai dati che nessun test interno elimina; per questo i vicini e il placebo sono obbligatori e R4 è dichiarata.
- Soglie assolute in $: lo stesso −3 vale −10% del prezzo a 30 $ e −1,5% a 200 $; nel 2020 (prezzi 1–5 $) R1 non può scattare.
- Dati spot Binance (BUSD nei primi mesi); nessun funding (solo spot); liquidità non remunerata.

---
# Estensione (27/11/2026, stessa preregistrazione, ancora prima di ogni rendimento)
Richiesta dell'utente: "Implementa la strategia nella 3.2 e fai check se serve nella strategia. Per SOL io utilizzando il MACD ho
avuto trade profittevoli. Creami una strategia coerente e profittevole."

**Prior dichiarato (lezione 79, research/macd_flip/).** I 7 trade dell'utente su SOL erano tutti incroci del MACD settimanale, ma la
stessa regola meccanica ne genera altri 5 in perdita (−56%, −27%, −28%, −34%, −20%) e due uscite (30 e 95 $) sono minimi visti col
senno di poi: ×52,6 la lista contro ×3,2 la regola sullo stesso periodo; parametri vicini azzerano SOL, dal 2024 nessuna variante
guadagnava. L'esperienza "trade profittevoli col MACD" è quindi attesa più debole come regola che come ricordo.

## 7. A · MACD dentro W3.2 (solo ricerca; `radar/weekly.py` non cambia)
- Motore: `motore.py` avvolge `weekly_bars` di W3.2 (nessuna copia del codice; stessa tecnica di w32_asset2/lib.csim). Verifica
  senza innesto (`verifica_motore.txt`): BTC dal 01/01/2021 84.820 $, ETH dal 11/01/2021 39.572 $, SOL dal 11/01/2021 80.661 $ =
  riferimenti, OK. Rischio 25%, trailing 2,5 ATRw, costi e funding come W3.2; dati `research/w32_asset2/crypto/data/`.
- MACD 12/26/9 sulla close settimanale (separato dal MACD 8/21/5 di F1, che resta). Soglie **in % del prezzo** con la conversione di
  R4 (P_IS SOL 32,11 $), **identiche per BTC, ETH e SOL**: "−3" = −9,34%, "+10" = +31,1%, "−50" = −155,7% della close.
  **Assolute** (−3 / +10 / −50 $) solo per SOL.
- **W-F (filtro)**: W3.2 entra long solo se linea < +10 equivalente; short solo se linea ≥ −3 equivalente.
- **W-U (uscita)**: W3.2 long esce anche quando la linea chiude ≥ +10 equivalente; short esce se la linea chiude ≤ −50 equivalente;
  uscita all'open del lunedì come le altre uscite di W3.2.
- Varianti: W-F% e W-U% su BTC, ETH, SOL (6 prove); W-F$ e W-U$ su SOL (2 prove).
- **"Serve" su BTC ed ETH** (tutto richiesto): CAGR/DD migliore della W3.2 base dal 2021 E in IS (→ 31/12/2022) E in OOS (dal
  01/01/2023) presi separatamente (corse che partono flat a inizio periodo); DD giornaliero non peggiore di 2 punti in ciascuno dei
  tre; WR sulle chiuse non più basso. Placebo (2.000 prove, seme 7): W-F = blocco casuale dello stesso numero di ingressi della base;
  W-U = uscita a una domenica casuale dentro lo stesso numero di trade della base; p = quota di prove con CAGR/DD ≥ variante.
- **"Serve" su SOL**: la variante rende SOL operabile con i criteri di sol_ciclo (dal 11/01/2021): CAGR/DD > B&H SOL e ≥ W3.2 ETH;
  DD ≥ −35%; WR chiuse ≥ 60%; positivo in IS, OOS e dal 2024; ≥ 8 trade; senza il trade migliore > 10.000 $; vicini trailing 2,0 e
  3,0 ATRw entrambi con CAGR/DD > B&H; placebo come sopra.
- Conteggi già noti (fase 1, `conteggi_innesti.txt`, sui segnali dei trade base, senza rendimenti): in % W-U non scatta mai su
  nessun asset (la linea non arriva a +31,1% del prezzo durante i trade W3.2) → W-U% è identica alla base; W-F% blocca solo short
  (BTC 1, ETH 3, SOL 6). In $ su SOL: W-F$ blocca 4 long e 5 short, W-U$ tocca 8 long su 15. Restano preregistrate così.

## 8. B · Strategia SOL costruita ("coerente e profittevole" = processo, non garanzia)
Costruzione SOLO su IS 11/01/2021 → 31/12/2022; giudizio SOLO su OOS dal 01/01/2023 e dal 2024. Tre candidati, definiti ora:
- **C1** = la variante fra R1–R4 con CAGR/DD IS più alto (corsa IS da 10.000 $ flat) + trailing di W3.2: stop iniziale close −
  2,5 ATRw (ATR 14 settimane, come W3.2), a cricchetto sul massimo delle close, controllato sui minimi giornalieri; 1x spot,
  tutto dentro; dopo un'uscita si rientra con la regola R della variante (di stato). Costi 0,2% per lato come §3.
- **C2** = W3.2 su SOL con cancello ETH (V2 di sol_ciclo, gate dalle posizioni W3.2 ETH calcolate dal 2020-06-01) + uscita W-U$
  (assoluta, la versione che su SOL scatta; rischio 25%, motore §7).
- **C3** = MACD ripartenza + trend: long all'open del lunedì dopo un incrocio al rialzo (linea > signal, la settimana prima ≤) con
  close > SMA 40 settimane; uscita all'incrocio al ribasso o alla close sotto la SMA 40; 1x spot, costi come §3.
- **Scelta** (unica, meccanica): CAGR/DD IS più alto fra C1–C3 con DD IS ≥ −35% e almeno 1 trade in IS; parità → meno trade.
  Se nessuno ha DD IS ≥ −35% non si sceglie nulla.
- **Giudizio** del solo candidato scelto, su una corsa che parte flat il 01/01/2023 con 10.000 $: CAGR/DD > B&H SOL dello stesso
  periodo; DD ≥ −35%; WR chiuse ≥ 60%; rendimento > 0 in OOS e dal 2024; ≥ 6 trade in OOS; senza il trade migliore > 10.000 $;
  vicini sopra il B&H in CAGR/DD in entrambi (C1 e C2: trailing 2,0 e 3,0 ATRw; C3: SMA 30 e 50); placebo come §5.8 sul periodo OOS.
- Se il candidato non passa: si scrive che **una strategia SOL profittevole e robusta non è stata trovata** e si propone solo il
  registro su carta (come sol_ciclo: ≥ 6 chiuse, WR ≥ 60%, rendimento positivo, DD ≥ −30% prima di qualsiasi denaro). Nessun
  secondo giro di candidati sugli stessi dati.

## 9. Correzione multipla (totale del PREREG)
Holm su tutte le prove con placebo: R1–R4 (4) + W-F%/W-U% × BTC/ETH/SOL (6) + W-F$/W-U$ SOL (2) + candidato B scelto (1) = **m = 13**,
α = 0,05. Le varianti con stop (R1s–R4s) e i riferimenti restano descrittivi. Le varianti oltre le 8 del metodo sono dichiarate
qui: tre famiglie (R, innesti, candidati B), ciascuna ≤ 8.
