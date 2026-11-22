# Swing su supporti/resistenze settimanali, stop 5–10% e TP 10–15% · azioni, indici, materie prime · 22/11/2026

**Verdetto: NON FUNZIONA fuori da BTC.** La configurazione scelta sul passato di ciascun asset è valida su **0 asset su 15** (ne
servivano 8); anche la configurazione unica per tutti è valida su 0/15 (PREREG beb05af, committato da solo prima di ogni
rendimento). Nessun placebo supera la correzione di Holm (p minimo 0,015, soglia 0,0033): gli ingressi sui livelli valgono
quanto ingressi a caso nello stesso regime. Nessuna configurazione scelta chiude sopra il buy & hold; una sola (BRK-B) lo
supera di un soffio in CAGR/DD (0,50 contro 0,49) ma con 19 trade non è valutabile. I guadagni che si vedono (11 asset su 15
sopra 10.000 $) sono la salita del mercato presa a metà: mediana 17.592 $ contro 70.204 $ del buy & hold. Nessuna modifica al tool.

## Cosa è stato provato
Stesse regole e stessi parametri di `research/swing_sr/` (motore `sw_engine.py` importato senza modifiche tramite
`swm_engine.py`; controllo: sulla serie BTC il wrapper riproduce 5.626 $ e 21.611 $ di `swing_sr/risultati.txt`, `controllo.txt`).
- Griglia: ingresso B/X/T × regime R0/R1 × lato L/S/LS × stop ST/SS/SF × uscita T10/T15/TSR/TH/TT = 270 configurazioni
  (R2 non esiste senza flusso perp).
- 15 asset, ognuno separato, 10.000 $ a 1x, una posizione per volta: SPY, QQQ, GLD, SLV, USO e 10 azioni. Dati giornalieri
  Yahoo fino al 20/11/2026, OHLC rettificati per split e dividendi. Costi: 0,05% per lato + 0,05% di slippage su ingressi e stop.
- Scelta sul periodo di scelta di ogni asset (fino al 2015; AVGO, TSLA, META metà/metà), giudizio una sola volta sul periodo
  successivo (2016 → 20/11/2026; AVGO dal 27/09/2018, TSLA dal 10/03/2019, META dal 17/02/2020).
- Esecuzione: `python3 swm_fetch.py` (dati), `swm_count.py` (conteggi), `swm_check.py` (controllo BTC), `swm_run.py` (~4 min)
  → `risultati.txt`, `griglia.csv`, `scelte.csv`, `placebo.csv`, `trade_scelte.csv`, `dimensioni.csv`; `swm_extra.py` → `extra.txt`.

## Risultati nel periodo di giudizio (10.000 $) · famiglia primaria, S\* scelta asset per asset
| Asset | S\* | Finale | DD | Trade | WR | PF | Buy & hold (DD) | Placebo p | Criteri falliti | Esito |
|---|---|---|---|---|---|---|---|---|---|---|
| SPY | X/R1/L/ST/T10 | 17.592 | −21,0 | 20 | 55 | 2,36 | 40.872 (−33,7) | 0,51 | 2, 3 | non valida |
| QQQ | X/R1/L/SS/TSR | 28.299 | −23,6 | 38 | 40 | 3,12 | 59.913 (−35,1) | 0,015 | 2, 3 | non valida |
| GLD | T/R0/L/ST/TT | 15.389 | −25,3 | 81 | 40 | 1,54 | 31.276 (−34,9) | 0,68 | 1, 2, 3 | non valida |
| SLV | B/R0/LS/SS/T15\* | 5.213 | −67,7 | 119 | 17 | 0,88 | 27.419 (−65,0) | 0,61 | 1–5 | non valida |
| USO | B/R0/LS/SF/T15\* | 4.334 | −80,4 | 64 | 31 | 0,88 | 15.485 (−86,8) | 0,60 | 1–5 | non valida |
| AAPL | X/R1/L/ST/TSR\* | 32.046 | −26,1 | 46 | 52 | 2,17 | 148.435 (−38,5) | 0,10 | 2, 3 | non valida |
| AMZN | T/R1/L/SS/TT\* | 7.412 | −35,8 | 54 | 30 | 0,78 | 75.142 (−56,1) | 0,88 | 1–5 | non valida |
| AVGO | T/R0/L/SS/TSR | 23.461 | −37,5 | 85 | 31 | 1,58 | 151.804 (−48,3) | 0,40 | 2, 3 | non valida |
| BRK-B | X/R1/L/SF/TH\* | 28.061 | −19,9 | 19 | 79 | 4,47 | 43.748 (−29,6) | 0,11 | 0, 3 | non valutabile |
| GOOGL | X/R1/L/ST/TSR\* | 25.285 | −27,4 | 43 | 44 | 1,92 | 70.204 (−44,3) | 0,25 | 2, 3 | non valida |
| LLY | X/R0/L/SS/T15\* | 38.123 | −32,5 | 100 | 26 | 1,76 | 192.737 (−34,5) | 0,19 | 1, 2, 3 | non valida |
| META | T/R1/LS/SF/T10 | 8.745 | −51,0 | 44 | 41 | 1,02 | 26.488 (−76,7) | 0,81 | 1–5 | non valida |
| MSFT | B/R1/L/SF/T10\* | 30.972 | −21,1 | 35 | 66 | 2,28 | 102.610 (−37,1) | 0,73 | 2, 3 | non valida |
| NVDA | X/R1/L/ST/T10\* | 16.952 | −50,1 | 84 | 44 | 1,29 | 1.595.889 (−66,3) | 0,92 | 2, 3 | non valida |
| TSLA | X/R0/LS/ST/T10\* | 12.430 | −73,9 | 156 | 40 | 1,13 | 182.778 (−73,6) | 0,21 | 1–4 | non valida |
| **Mediana** | | **17.592** | −32,5 | 54 | 40 | 1,58 | **70.204** (−44,3) | 0,51 | | **0/15 valide** |

\*Nessuna configurazione ammissibile nel periodo di scelta (≥ 30 trade, PF ≥ 1,2 nelle due metà, DD entro −20%): come da PREREG
è stata presa quella con il CAGR/DD più alto fra quelle con ≥ 30 trade. Succede su 10 asset su 15.
Criteri: 0 = ≥ 20 trade · 1 = positiva con PF ≥ 1,2 nelle due metà · 2 = DD entro −20% · 3 = placebo con Holm · 4 = senza i 2
trade migliori · 5 = vicini (K = 2, K = 4, vita dei livelli 52 e 156 settimane). Superati su 15: 14 · 8 · 1 · 0 · 10 · 11.

**Famiglia secondaria, G\* = B/R1/L/SS/TT per tutti** (rimbalzo, trend, solo long, stop strutturale, solo trailing; ammissibile
su 2 asset in scelta): 0/15 valide. Mediana 13.897 $, DD −25,5%, PF 1,57, WR 34%; sopra 10.000 $ su 13 asset, DD entro −20% su 3
(SPY 13.000 $, QQQ 19.527 $, GLD 17.310 $), placebo p minimo 0,015, p ≤ 0,05 su 1/15; finale sopra il buy & hold su 0/15.

**Dal 01/01/2021** (finestra abituale, descrittivo): S\* mediana 11.982 $ contro 22.857 $ del buy & hold; sopra il buy & hold
su 1 asset su 15 (QQQ: 20.070 contro 19.945 $).

## Cosa dicono i dati
- **I livelli non danno il momento d'ingresso.** Placebo: p mediano 0,51 (S\*) e 0,27 (G\*); il risultato reale supera la
  mediana degli ingressi casuali su 7 e 8 asset su 15, cioè come una moneta. Con 30 test, un solo p ≤ 0,05 per famiglia è quanto
  ci si aspetta dal caso.
- **Il guadagno è il mercato, non la strategia.** Solo long: mediana 21.511 $, positive il 90%. Solo short: 5.019 $, positive
  l'1% (PF 0,46). Long e short: 10.896 $. S\* sta in posizione il 46% del tempo e incassa una frazione della salita.
- **Contro il buy & hold perde quasi sempre.** Su 4.050 coppie asset × configurazione: finale sopra il buy & hold 0,8%,
  CAGR/DD sopra il buy & hold 5,2%, DD entro −20% solo il 3% (fra i soli long: 2,2%, 14%, 9%). Tagliare a +10/15% su azioni
  che fanno ×10–×160 è il costo principale, come su BTC dentro il regime di W3.1.
- **Stop** (finale mediano, tutte le configurazioni): ST 9.966 $ · SF 9.952 $ · SS 9.378 $; migliore su 4 / 5 / 6 asset. Fra i
  soli long: SF 23.718 $ (WR 54%) · ST 22.181 $ (WR 45%) · SS 19.205 $ (WR 32%). Lo stop oltre il livello è sotto il 5% nel
  77–100% dei segnali (mediana 1,9–3,4% secondo l'asset): "5–10%" diventa uno stop fisso al 5%, e lo stop stretto al livello è il peggiore.
- **Uscite**: T15 10.470 $ · TSR 9.966 $ · TH 9.880 $ · TT 9.410 $ · T10 9.128 $; nessuna prevale (migliore su 4 / 5 / 0 / 5 / 1
  asset). Fra i soli long TSR 24.762 $ e T15 23.481 $ contro T10 20.451 $ e TT 19.374 $: il TP più lontano rende di più, il
  trailing a 3 ATR giornalieri di meno.
- **Ingresso e regime**: rottura X 11.404 $ (migliore su 12 asset) contro B 8.946 $ e T 8.964 $; R1 11.205 $ (DD −38%) contro
  R0 7.783 $ (DD −61%). Il trend di prezzo riduce il DD, non crea vantaggio (i placebo sono nello stesso regime).
- **La classifica del passato predice solo il lato.** Correlazione di rango scelta → giudizio 0,61 in mediana su tutte le
  configurazioni, ma −0,07 dentro i soli long (aggiunta non preregistrata): dice "long meglio di short in un mercato che
  sale", non quale ingresso, stop o uscita scegliere.
- **Costi**: non spiegano il risultato. S\* a costi zero 19.686 $ in mediana, a costi doppi 16.996 $.
- **Materie prime**: su SLV e USO la scelta perde metà del capitale (5.213 e 4.334 $, DD −68/−80%); conferma le lezioni 75 e 76.

## Deviazioni dal PREREG e cose non verificate
1. `swm_run.py`, `swm_check.py` e `swm_extra.py` sono stati scritti dopo il commit del PREREG e non sono committati (l'agente
   committa solo il PREREG). `swm_run.py` è stato provato a secco su 3 serie casuali (`--dry`) prima dell'unica esecuzione reale.
2. Criterio 1 applicato nella lettura più severa (anche ciascuna metà sopra 10.000 $). Senza effetto: il criterio 3 è 0/15.
3. `swm_extra.py` (rango dentro i soli long, mediane dei soli long, 3 trade ricalcolati a mano: coincidono) non era nel PREREG.
4. Correlazione di rango calcolata sui ranghi con Pearson (equivalente a Spearman). K = 3 e gli altri parametri sono ereditati da BTC.
5. Nel placebo i trade simulati sono in mediana 0–10% meno di quelli reali (SLV 107 contro 119): effetto non misurato.
6. Controllo di qualità dei dati (barre piatte, OHLC incoerenti, prezzi negativi) fatto con uno script non salvato.
7. **Non eseguiti**: revisione critica di un agente separato; verifica dei dati Yahoo contro una seconda fonte; secondo ciclo.

## Limiti
- Costo del prestito titoli per gli short non modellato; liquidità non remunerata (sfavorisce la strategia nei periodi fuori mercato; effetto non
  misurato); prezzi rettificati per i dividendi (i livelli storici sono leggermente spostati).
- Le 10 azioni sono vincitrici scelte ex post: il buy & hold è eccezionale e i long sono favoriti. Il placebo non ne risente.
- USO è un ETF su future WTI con costo di rollover, non il Brent; i future continui (BZ=F, CL=F, GC=F, SI=F) sono stati
  esclusi per barre piatte, OHLC incoerenti e prezzo negativo del 2020. Indici non USA non testati.
- Barre giornaliere (nessun ingresso intragiornaliero sul livello), una sola definizione di livello, periodo di giudizio
  quasi tutto rialzista per azioni e oro: gli short non sono stati messi alla prova in un ribasso lungo.
- Con DD −20% come soglia la maggior parte delle azioni non ha configurazioni ammissibili: la soglia è quella dello stile
  richiesto, ma su titoli singoli a 1x è quasi irraggiungibile.

## Lezione proposta per RESEARCH.md
**Lezione 107**: lo swing breve sui livelli settimanali con stop 5–10% e TP 10–15% non funziona nemmeno su azioni, indici e
materie prime (SPY, QQQ, GLD, SLV, USO, 10 azioni; scelta fino al 2015, giudizio 2016–2026): 0 asset su 15 validi sia con la
configurazione scelta asset per asset sia con una sola per tutti; nessun placebo supera Holm (p mediano 0,51) e nessuna scelta
chiude sopra il buy & hold (mediana 17,6k contro 70,2k). I long guadagnano perché il mercato sale (90% positive), gli short
perdono (1% positive), e la classifica del passato predice solo il lato (rango 0,61 su tutte, −0,07 fra i soli long). Lo stop
al livello è quasi sempre sotto il 5% ed è il peggiore; il TP più lontano rende più di quello a +10%. Su argento e petrolio la
scelta dimezza il capitale. Con le lezioni 75–77 e 106 l'idea è chiusa su tutte le classi provate; un test multi-asset va
giudicato contro il buy & hold e contro ingressi casuali nello stesso regime, non contro i 10.000 $ di partenza.
research/swing_sr_multi/README.md (22/11/2026, revisione critica separata non eseguita).

## Revisione critica (agente separato, 22/11/2026)
Il verdetto regge. Verifiche eseguite dal revisore con script propri, non salvati nel repo: 239 trade rigiocati barra per barra
(MSFT, LLY, SPY, NVDA) coincidono per data, motivo d'uscita e P&L; nessuna informazione dal futuro (i livelli entrano con un giorno
di ritardo: prudente); i prezzi rettificati non falsano stop e TP in percentuale. Il risultato positivo di alcuni asset è beta di
mercato: il finale supera il buy & hold scalato alla quota di tempo in posizione su 4 asset su 15 (QQQ, BRK-B, GOOGL, MSFT), il
rapporto mediano è 0,84 e il CAGR/DD lo supera su 1 su 15. QQQ: 28,3k contro 25,1k del buy & hold scalato. Su QQQ, AAPL, BRK-B,
MSFT e LLY i primi 3 trade valgono il 32–41% del guadagno. p combinato di Fisher sui placebo: 0,27.
