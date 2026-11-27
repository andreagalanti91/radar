# MACD settimanale 12/26/9 su SOL · "Buy da −3 a −50, Sell da +10" · fase 2 (27/11/2026)

**Verdetto: nessuna regola MACD è valida su SOL e il MACD non serve dentro W3.2. Una strategia SOL profittevole e robusta non è
stata trovata: si propone solo il registro su carta.** PREREG `a5f2206` (committato da solo), conteggi `a72c975`; esecuzione senza
modifiche (`fase2.py`, punti tecnici in `DEVIAZIONI.md`). Nessuna prova passa la correzione di Holm (m = 13, p minimo 0,09).

| Blocco | Esito | Perché, in breve |
|---|---|---|
| R1–R4 (regola dell'utente e varianti) | **descrittive, tutte bocciate** | 1–3 trade in 6 anni (servono ≥ 8); DD −79/−95%; sotto il B&H |
| W-F / W-U dentro W3.2 · BTC | **non serve** | W-F toglie 1 short e peggiora (CAGR/DD 1,84 contro 2,07); W-U non scatta mai |
| W-F / W-U · ETH | **non serve** | W-F migliora i numeri (0,98 contro 0,96, WR 64% contro 57%) ma è compatibile col caso (placebo p 0,27); W-U mai attiva |
| W-F / W-U · SOL | **non rende SOL operabile** | il migliore (W-F in $) fa 105.202 $ ma DD −37,3% e WR 54%; nessuno supera i criteri di sol_ciclo |
| Candidato B scelto in IS: C2 (W3.2 + cancello ETH + uscita MACD ≥ +10 $) | **bocciato in OOS** | batte il B&H per rischio (1,04 contro 0,85) ma vince 3 su 7, i vicini scendono sotto il B&H, placebo p 0,09 |

## 1. Confronto (10.000 $, 1x, costi 0,2% per lato; R dal 07/12/2020, in pratica come dal 2021: nessun segnale prima)
| Strategia | Finale | Rend. | DD giorn. | CAGR/DD | Trade | WR chiuse | IS → 2022 | OOS 2023→ | Dal 2024 |
|---|---|---|---|---|---|---|---|---|---|
| R1 letterale | 8.292 $ | −17% | −93,0% | −0,03 | 3 | 50% (1/2) | −89% | +656% | +1% |
| R2 ripartenza | 20.224 $ | +102% | −79,3% | 0,16 | 3 | 100% (2/2) | −77% | +761% | +15% |
| R3 istogramma | 3.866 $ | −61% | −95,1% | −0,15 | 1 (aperto) | – | −95% | +599% | −32% |
| R4 normalizzata | 8.223 $ | −18% | −93,0% | −0,03 | 1 (aperto) | – | −88% | +599% | −32% |
| B&H SOL dal 07/12/2020 | 374.895 $ | +3.649% | −96,3% | 0,87 | – | – | +446% | +599% | −32% |
| B&H SOL dal 01/01/2021 · dal 11/01/2021 | 460.046 · 201.456 $ | | −96,3% | 0,95 · 0,69 | | | | | |
| Flip MACD solo long (lez. 79, ricostruito) | 643.404 $ | +6.334% | −84,8% | 1,19 | 8 | 62% | | | |
| W3.2 SOL dal 11/01/2021 (sol_ciclo) | 80.661 $ | +707% | −39,8% | 1,07 | 23 | 45% | | | −10% |
| W3.2 BTC dal 01/01/2021 | 84.820 $ | +748% | −21,1% | 2,07 | 14 | 92% | | | |
| C2 (candidato B), solo OOS dal 01/01/2023 | 21.454 $ | +115% | −20,8% | 1,04 | 8 | 43% (3/7) | – | +115% | +8% |
| B&H SOL dal 01/01/2023 | 69.621 $ | +596% | −76,3% | 0,85 | – | – | – | | |

Per anno R1: 2022 −89% · 2023 +650% · 2024 0% · 2025 +80% · 2026 −44%. R2: 2022 −77% · 2023 +650% · 2025 +38% · 2026 −17%.
Robustezza R: vicini (banda ×0,5 / ×2, vendita +5 / +20) sopra il B&H 0 su 4 per tutte; senza il trade migliore R1 4.371 $, R2 11.458 $;
placebo p R1 0,70, R2 0,49, R3 0,96, R4 0,67. R3 e R4 entrano una volta (19/12/2021 e 07/03/2022) e non escono più: sono un buy &
hold iniziato vicino al massimo. **Con stop −20% (solo riferimento di rischio)**: R1s 14.983 $ (DD −83%, 13 trade, WR 17%), R2s 5.059 $
(DD −54%, WR 0%), R3s 416 $ (14 stop di fila), R4s 17.818 $ (DD −84%): lo stop non salva la regola, la fa uscire e rientrare nel ribasso.
Il flip solo long (lezione 79: 859.841 $ con dati fino al 05/11 e costi 0,1%) batte il B&H per rischio ma con DD −85%: non operabile.

### Operazioni R1 (letterale)
| n | Entrata | Prezzo | Uscita | Prezzo | Motivo | Giorni | Risultato | Conto dopo |
|---|---|---|---|---|---|---|---|---|
| 1 | 21/02/2022 | 90,79 | 11/12/2023 | 74,81 | linea ≥ +10 | 658 | −17,8% | 8.223 $ |
| 2 | 17/03/2025 | 126,26 | 15/09/2025 | 239,51 | linea ≥ +10 | 182 | +89,3% | 15.568 $ |
| 3 | 24/11/2025 | 130,71 | aperta (24/11/2026: 69,69) | | | 365 | −46,8% | 8.275 $ |
Il trade 1 attraversa tutto il 2022: il conto sale a ~15.000 $ il 03/04/2022, scende a ~1.060 $ il 29/12/2022 (SOL 9,64 $; DD −93%) e chiude in perdita un anno dopo.

### Operazioni R2 (ripartenza)
| n | Entrata | Prezzo | Uscita | Prezzo | Motivo | Giorni | Risultato | Conto dopo |
|---|---|---|---|---|---|---|---|---|
| 1 | 01/08/2022 | 42,38 | 11/12/2023 | 74,81 | linea ≥ +10 | 497 | +76,1% | 17.615 $ |
| 2 | 19/05/2025 | 173,47 | 15/09/2025 | 239,51 | linea ≥ +10 | 119 | +37,8% | 24.272 $ |
| 3 | 20/04/2026 | 83,55 | aperta (24/11/2026: 69,69) | | | 218 | −16,8% | 20.184 $ |
Vince 2 su 2 chiuse, ma il trade 1 passa per un −79% (FTX) prima di guadagnare: 3 trade in 6 anni non sono una prova.

## 2. MACD dentro W3.2 (rischio 25%, stessi dati e motore di W3.2; verifica senza innesto: 84.820 / 39.572 / 80.661 $)
| Innesto | Finale (base) | DD (base) | CAGR/DD (base) | WR chiuse (base) | CAGR/DD IS · OOS (base) | Trade cambiati | Placebo p | Esito |
|---|---|---|---|---|---|---|---|---|
| W-F% BTC | 78.297 (84.820) | −22,8 (−21,1) | 1,84 (2,07) | 92 (92) | 2,84 · 2,04 (3,72 · 1,33) | 1 short | 0,66 | non serve |
| W-U% BTC | = base | | | | | 0 | 1 | non serve (inerte) |
| W-F% ETH | 40.632 (39.572) | −27,5 (−27,5) | 0,98 (0,96) | 64 (57) | 3,11 · 0,77 (2,30 · 0,64) | 3 short | 0,27 | non serve (criteri sì, placebo no) |
| W-U% ETH | = base | | | | | 0 | 1 | non serve (inerte) |
| W-F% SOL | 88.597 (80.661) | −39,8 (−39,8) | 1,13 (1,07) | 50 (45) | – | 7 | 0,26 | non operabile (DD, WR, dal 2024 −6%, vicini) |
| W-U% SOL | = base | | | | | 0 | 1 | non operabile (inerte) |
| W-F$ SOL | 105.202 | −37,3 | 1,32 | 54 | – | 9 | 0,14 | non operabile (DD −37,3%, WR 54%) |
| W-U$ SOL | 61.976 | −32,5 | 1,12 | 48 | – | 4 | 0,45 | non operabile (WR 48%, vicini 0,38 / 1,10) |
In % del prezzo l'uscita "+10 equivalente" (+31,1% del prezzo) non si raggiunge mai durante un trade W3.2: W3.2 esce prima
(trailing, EMA21, distribuzione). Il filtro tocca solo short. Su SOL le versioni in $ cambiano di più, ma solo perché le soglie
assolute scattano ai prezzi 2024–25; W-F$ migliora l'OOS (CAGR/DD 1,48 contro 0,57) e peggiora l'IS (2,91 contro 3,50).

## 3. Strategia SOL costruita (scelta in IS 11/01/2021 → 2022, giudizio solo dal 2023)
| Candidato (definito nel PREREG) | IS: finale | DD | CAGR/DD | Trade |
|---|---|---|---|---|
| C1 = R2 (migliore R in IS) + trailing 2,5 ATRw | 4.783 $ | −56,5% | −0,55 | 1 |
| **C2 = W3.2 + cancello ETH + uscita MACD ≥ +10 $** | 25.110 $ | **−16,6%** | **3,60** | 6 |
| C3 = incrocio al rialzo sopra SMA40, uscita incrocio al ribasso o sotto SMA40 | 32.167 $ | −35,2% (escluso) | 2,30 | 1 |
Giudizio di C2 dal 01/01/2023: CAGR/DD 1,04 > 0,85 B&H ✓ · DD −20,8% ✓ · WR chiuse 43% ✗ · +115% OOS e +8% dal 2024 ✓ · 8 trade ✓ ·
senza il migliore 10.758 $ ✓ · vicini trailing 2,0 / 3,0: 0,78 / 0,88, serve > 0,85 in entrambi ✗ · placebo p 0,09 ✗ (anche senza Holm).
Descrittivo, fuori dal giudizio: C3 in OOS 44.525 $ con DD −47,8% e 4 trade; C1 14.933 $ con DD −36%: nessuno dei due avrebbe passato.

### Operazioni C2 (OOS, dal 01/01/2023, 10.000 $)
| n | Lato | Entrata | Prezzo | Uscita | Prezzo | Motivo | Esposizione | Risultato sul conto | Conto dopo |
|---|---|---|---|---|---|---|---|---|---|
| 1 | long | 30/10/2023 | 32,86 | 11/12/2023 | 74,81 | MACD ≥ +10 $ | 0,78 | +99,4% | 19.937 $ |
| 2 | long | 11/11/2024 | 210,28 | 18/11/2024 | 237,23 | MACD ≥ +10 $ | 0,74 | +9,4% | 21.806 $ |
| 3 | long | 21/07/2025 | 181,62 | 04/08/2025 | 161,82 | EMA21 | 0,63 | −7,0% | 20.284 $ |
| 4 | long | 01/09/2025 | 200,82 | 15/09/2025 | 239,51 | MACD ≥ +10 $ | 0,66 | +12,5% | 22.825 $ |
| 5 | long | 22/09/2025 | 236,40 | 29/09/2025 | 210,62 | MACD ≥ +10 $ | 0,78 | −8,7% | 20.843 $ |
| 6 | short | 25/05/2026 | 85,18 | 21/08/2026 | 90,49 | trailing | 0,54 | −3,4% | 20.140 $ |
| 7 | long | 31/08/2026 | 101,85 | 02/11/2026 | 94,45 | EMA21 | 0,79 | −5,9% | 18.949 $ |
| 8 | short | 09/11/2026 | 86,45 | aperta (69,69) | | | 0,69 | +13,2% | 21.448 $ |
Il risultato è il trade 1 (da 10.000 a 19.937 $); poi sette operazioni per +8% in tre anni. Il trade 1 è uscito per MACD ≥ +10 $ a 74,81 $: W3.2 base
(sol_ciclo) nello stesso rialzo era entrata il 02/10/2023 a 23,90 $ e usciva il 01/01/2024 a 101,62 $ (+192% sul conto).

## 4. Cosa abbiamo imparato
- **Le soglie in dollari sul MACD non hanno senso su un asset che passa da 10 a 250 $.** −3 $ è −15% del prezzo a 20 $ e −1,5% a
  200 $; il −50 non è mai stato toccato (minimo −24 $). La regola diventa "compra appena il MACD è sotto −3": nel 2022 compra a 91 $
  all'inizio del ribasso e tiene fino a 10 $ (−93%), perché la vendita a +10 $ non arriva finché il prezzo è basso.
- **"MACD negativo = sconto" è un coltello che cade**: tutte le varianti sono in perdita o quasi in IS (−77/−95%) e guadagnano solo
  perché il 2023 ha moltiplicato SOL per 10. Lo stop −20% non aiuta: esce e rientra nel ribasso (R3s: 14 stop di fila).
- **Normalizzare non salva l'idea**: R4 compra una volta nel 2022 e non vende più; diventa un buy & hold partito tardi.
- **Dentro W3.2 il MACD alto non serve come uscita**: W3.2 esce prima per conto suo; dove scatta (SOL in $) taglia anche i grandi
  trend (uscita a 74,81 $ il 11/12/2023; W3.2 base usciva a 101,62 $ il 01/01/2024). Come filtro tocca solo pochi short e il miglioramento su ETH è compatibile col caso.
- **La parte "buona" del MACD su SOL resta l'incrocio, non il livello**: il flip solo long fa 643k $ (CAGR/DD 1,19 > B&H 0,87), ma
  con DD −85% e un risultato dovuto a due rialzi (2021 e fine 2023): conferma la lezione 79, non la ribalta.
- **Costruire in IS non basta**: il candidato con l'IS migliore (C2, CAGR/DD 3,60, WR 80%) in OOS vince 3 volte su 7 e vive di un trade.

## 5. Cosa significa per l'utente
- La regola "compra con MACD da −3 a −50, vendi da +10" su SOL avrebbe portato 10.000 $ a 8.292 $ con un calo intermedio del 93%:
  **non va usata**, né con lo stop né normalizzata. I trade profittevoli ricordati col MACD sono incroci scelti a posteriori (lezione 79).
- **W3.2 resta com'è**: il MACD 12/26/9 non aggiunge nulla su BTC ed ETH.
- **Su SOL non c'è oggi una strategia robusta e profittevole**: nessun denaro. Unica proposta: il registro su carta già previsto da
  sol_ciclo (V2, W3.2 con cancello ETH), con accanto la colonna C2 (stessa regola + uscita MACD ≥ +10 $) per vedere dal vivo se
  l'uscita MACD aiuta; rivalutazione solo dopo ≥ 6 chiuse con WR ≥ 60%, rendimento positivo e DD ≥ −30%.

## 6. Limiti
SOL ha storia dal 04/2020 (utilizzabile da 12/2020): un solo ciclo completo; R1–R4 fanno 1–3 trade, quindi i loro numeri sono
aneddoti. Le soglie dell'utente sembrano scelte sui prezzi 2024–26 (rischio di adattamento); proprio lì R1/R2 vincono (+89%, +38%).
Dati spot Binance (BUSD nei primi mesi), liquidità a 0%, nessun funding sulle regole a sé; C2 e innesti con funding reale come W3.2.
13 prove con placebo: anche un p di 0,01 non sarebbe bastato con Holm.

## 7. Lezione 130 proposta (per RESEARCH.md)
**Lezione 130**: MACD settimanale 12/26/9 su SOL "compra da −3 a −50, vendi da +10" (research/macd_sol, PREREG a5f2206; 4 regole, 8
innesti in W3.2, 3 candidati costruiti in IS, Holm m = 13): niente funziona. Le soglie in dollari pesano 10 volte di più a 20 $ che a
200 $: la regola letterale compra all'inizio del bear 2022 e chiude a 8.292 $ (DD −93%, 3 trade; B&H 374.895 $); normalizzata o con
stop −20% non migliora. Dentro W3.2 il MACD non serve: l'uscita "+10 equivalente" non scatta mai su BTC/ETH (W3.2 esce prima), il
filtro tocca pochi short (ETH meglio ma placebo p 0,27). Il candidato SOL scelto in IS (W3.2 + cancello ETH + uscita MACD ≥ +10 $,
CAGR/DD IS 3,60) in OOS fa 21.454 $ con WR 43%, vicini sotto il B&H, placebo p 0,09. Il livello del MACD non è un segnale; su SOL solo
registro su carta.
