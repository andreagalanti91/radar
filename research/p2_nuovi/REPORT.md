# Parte 2 e pre-analisi giornaliera — report 19/11/2026

## Conclusione
1. Nessun indicatore nuovo migliora i segnali di W3: opzioni (DVOL/VRP, skew), ETH/BTC, dominanza, vol targeting e piramidazione
   sono respinti; il picco di DVOL rientrato (O2) resta solo su carta (10 trade, placebo non superato).
2. La leva che conta è la dimensione della posizione. Con la delega dell'utente, la regola preregistrata ha scelto: **rischio allo
   stop 10%** (era 25%), stop e trailing invariati (2,5 ATR settimanali), nessun take profit. Applicata al tool: W3.1.
3. La pre-analisi giornaliera e il riepilogo Telegram "Oggi" sono online.

## Dimensione della posizione (stessi segnali, dal 2021, 10k)
| Rischio allo stop | 10k → | DD 2021+ | DD 2018–20 | CAGR/DD | P(DD ≥ 30%) |
|---|---|---|---|---|---|
| 5% | 16,8k | −5,4% | −10,7% | 1,72 | 0% |
| **10% (W3.1)** | **27,2k** | **−9,8%** | **−19,2%** | **1,90** | **0,7%** |
| 15% | 42,6k | −13,9% | −26,3% | 2,01 | 8% |
| 20% | 61,1k | −17,7% | −32,3% | 2,04 | 27% |
| 25% (W3) | 78,5k | −21,1% | −37,3% | 1,99 | 48% |
Nessuna configurazione ha soddisfatto tutti i vincoli preregistrati (OOS 2024–26 non peggiore di W3: 1,615 contro 1,639; vicini
instabili sul k ATR) → ripiego preregistrato: 10%, k 2,5. Il take profit parziale non migliora (lezione 73). Kelly non stimabile
(nessun trade perdente nel periodo di studio).

## Filtri e strategie nuove
| Regola | 10k dal 2021 | Esito |
|---|---|---|
| W3 invariata | 78.474 (DD −21,1%) | riferimento |
| O1 premio di volatilità implicita (VRP) | 19,9k–53,4k | respinta |
| O3 skew | 58,3k–70,0k | respinta (peggiora W3) |
| R1 ETH/BTC | 35,8k–38,8k | respinta |
| R2 dominanza BTC | 64,1k–69,1k | respinta |
| V vol targeting | 48,5k–65,1k (DD −32/−35%) | respinta |
| P1 piramidazione | 20,8k–32,5k | respinta |
| O2 picco DVOL rientrato (autonomo) | 14,2k (10 trade) | solo su carta |

## Short aperto dal 16/11
Con W3.1 l'esposizione raccomandata è **0,389** invece di 0,972 (perdita allo stop ≈ 10% della quota invece di ≈ 25%).
Stop/trailing invariato (81.695 $). Il tool mostra già piano e P&L su 0,389.

## Pensiero dirompente (research/dirompente/)
Rischio per trade troppo alto e comunicazione ottimistica (lezione 99): risolto il primo con W3.1; i numeri comunicati ora sono
27,2k / −9,8% con la perdita allo stop in evidenza.

## Pre-analisi giornaliera
Online nel riquadro Pre-analisi (posizione W3 dal vivo, contesto di oggi con affidabilità, S/R con tenuta storica vs casuale,
situazioni simili con IC) e riepilogo Telegram giornaliero all'01:00 italiana.
