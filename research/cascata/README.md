# Uscita di profitto nel giorno di "cascata a favore" e rientro su W3.2 · BTC (+ ETH) · 23/11/2026

**Verdetto: non regge. 0 varianti su 6 passano i criteri (PREREG `9e437db`, committato da solo prima di ogni rendimento).
W3.2 resta invariata, nessuna modifica a radar/.**
- Uscire all'apertura dopo una cascata a favore e rientrare porta 10.000 $ a 34–73k $ contro 78.474 $; il drawdown non scende
  (−21,1/−25,6% contro −21,1%). Nessuna variante migliora insieme 2021–23 e 2024–26; la somma dei Δ per trade è negativa in tutte.
- A 55.130 $ non si poteva chiudere: è il minimo di una candela, noto solo dopo. L'uscita eseguibile era l'apertura del 22/11
  a circa 60.280 $. Un ordine a limite abbastanza vicino da essere preso il 20–21/11 (1,25–1,5 ATR giornalieri) nello storico
  fa 20–30k $ con DD −30/−34%: taglia tutti i trend.
- "Dopo una cascata BTC rimbalza": non confermato. Dopo un giorno di crollo in chiusura (≥ 2 ATR, volume ≥ 2×) BTC nei 7
  giorni successivi è sceso ancora (−4,2% in media, 3 casi positivi su 12). Dopo un crollo con rifiuto (tipo 21/11) l'effetto è nullo.
- Potenza bassa (13 trade, 5–12 toccati dall'evento): vale "nessun miglioramento dimostrabile", non "impossibile".

## Risposta diretta all'utente
1. **Chiudere a 55?** No, perché non era un prezzo disponibile a una regola: il 21/11 il minimo è durato un'ora e il giorno ha
   chiuso in rialzo (60.216 $). Qualsiasi regola giornaliera avrebbe chiuso a ~60.280 $ (apertura del 22/11).
2. **In questo caso uscire a 60.280 $ avrebbe reso di più** (finora): su 50.000 $ fra +590 e +2.640 $ rispetto al tenere, perché
   BTC è risalito a 63.850 $. È un caso solo e il trade non è finito.
3. **Sullo storico la stessa regola costa**: applicata a tutti i 13 trade dal 2021 toglie 5–44k $ su 78k. Dopo una cascata a
   favore il trend di solito prosegue (10 volte su 14 a 7 giorni, +5% medio; estremo migliore in seguito 13 volte su 14). W3.2
   poi ne restituisce una parte (esce peggio dell'apertura successiva 9 volte su 14), ma il rientro una settimana dopo compra
   peggio e con un nuovo stop: i rientri finali perdono −5/−14% (2022-11 −14,1%, 2026-06 −12,4%, 2026-02 −9,0%, 2023-03 −7,5%, 2024-11 −5,4%).
4. **Decidere giorno per giorno sulle posizioni weekly?** I dati dicono di no, per la quarta volta (lezioni 105, 109, 114 e questa):
   TP fissi, livelli, flusso spot/perp e ora cascate. Il controllo giornaliero utile resta il trailing a 2,5 ATR settimanali
   (oggi 75.764 $) e la decisione della domenica. Se l'obiettivo è "incassare qualcosa" nei giorni di cascata, la forma meno
   costosa è la metà (C4: 73,0k $, WR 100%, DD uguale), ma equivale a ridurre il rischio (lezione 109) e peggiora il 2018–20.

## Definizioni (fissate prima; grandezze note alla chiusura del giorno)
atr1 = ATR14 giornaliero del giorno prima; vr = volume spot+perp / media dei 30 giorni precedenti.
- **D1 cascata in chiusura**: rendimento a favore ≥ 2 atr1 e vr ≥ 2 (soglie dell'incarico).
- **D3 cascata con rifiuto**: escursione a favore ≥ 1,25 atr1, vr ≥ 2, chiusura che restituisce ≥ 50% dell'intervallo del giorno.
  Soglie tagliate sul 21/11 (definizione "su misura", la più favorevole all'ipotesi; il 21/11 è fuori dal campione del test).
- **LIM**: ordine a limite a 2 atr1 a favore dalla chiusura precedente, rinnovato ogni giorno (senza volume: non è noto prima).
- Uscita all'apertura successiva (mai al minimo). R1 = rientro alla domenica successiva se il segnale W3.2 è vero; R2 = R1 +
  rientro dopo un rimbalzo del 5% dal prezzo d'uscita con regime valido; R3 = nessun rientro fino alla fine del trade originale.

## Risultati (10.000 $, 1x, costi e rischio 25% di W3.2; IS, OOS, 2018–20 ed ETH ripartono da 10.000 $)
| Variante | Finale 2021+ | CAGR | DD | CAGR/DD | Trade | WR | Peggiore | Uscite | IS fin. / CDD | OOS fin. / CDD | 2018–20 fin. / DD / CDD | ETH fin. / CDD | ΣΔ log (senza 2) | p segni | p placebo |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **W3.2 (in uso)** | **78.474** | 42,0 | −21,1 | 1,990 | 13 | 92,3 | −4,1 | — | 33.477 / 2,574 | 23.488 / 1,639 | 25.142 / −37,3 / 0,966 | 37.575 / 0,919 | — | — | — |
| C1 D1 tutto, R1 (primaria) | 53.945 | 33,3 | −24,6 | 1,351 | 23 | 73,9 | −14,1 | 12 | 25.688 / 1,504 | 21.042 / 1,399 | 27.504 / −30,4 / 1,319 | 39.886 / 0,910 | −37,5 (−57,3) | 0,90 | 0,32 |
| C2 D1 tutto, R2 5% | 50.670 | 31,8 | −25,6 | 1,242 | 25 | 72,0 | −14,1 | 12 | 24.550 / 1,364 | 20.681 / 1,362 | 28.024 / −38,1 / 1,076 | 32.462 / 0,761 | −43,7 (−54,1) | 0,96 | 0,68 |
| C3 D1 tutto, R3 | 65.749 | 37,8 | −21,1 | 1,790 | 13 | 100 | +4,3 | 9 | 27.885 / 2,274 | 23.579 / 1,647 | 13.926 / −34,7 / 0,337 | 46.520 / 1,088 | −17,7 (−45,0) | 0,67 | 0,94 |
| C4 D1 metà | 73.011 | 40,3 | −21,1 | 1,908 | 13 | 100 | +3,5 | 9 | 30.871 / 2,545 | 23.677 / 1,656 | 19.027 / −31,6 / 0,757 | 42.010 / 1,007 | −7,2 (−21,3) | 0,65 | 0,77 |
| C5 D3 tutto, R1 | 70.568 | 39,5 | −21,1 | 1,869 | 20 | 80,0 | −9,0 | 8 | 29.765 / 2,275 | 23.756 / 1,664 | 23.006 / −37,3 / 0,860 | 42.701 / 0,924 | −10,6 (−31,0) | 0,63 | 0,036 |
| C6 LIM 2 ATR tutto, R1 | 34.500 | 23,5 | −23,8 | 0,989 | 31 | 74,2 | −15,5 | 21 | 19.310 / 1,034 | 17.902 / 0,958 | 23.087 / −30,4 / 1,058 | 23.448 / 0,437 | −82,2 (−102,7) | 0,97 | 0,20 |
| Buy & hold | 22.549 | 14,9 | −76,6 | 0,194 | — | — | — | — | 14.590 / 0,175 | 15.425 / 0,307 | 21.046 / −81,2 / 0,347 | 24.873 / 0,212 | — | — | — |

Criteri (8): C1 IS e OOS migliori **0/6** (l'IS peggiora sempre: 1,03–2,55 contro 2,57) · C2 2018–20 non peggiore 3/6 (C1, C2,
C6) · C3 DD entro −30% 6/6 · C4 WR ≥ 70% 6/6 · C5 non dipende da ≤ 2 trade **0/6** (ΣΔ negativa già con tutti i trade) ·
C6 Holm **0/6** (p 0,63–0,97) · C7 placebo 1/6 (C5) · C8 ETH 3/6 (C3, C4, C5). **Nessuna variante passa.**
- Senza il trade migliore: W3.2 51.561 $; varianti 27.653–47.971 $.
- C5 batte il placebo (p 0,036): i giorni "con rifiuto" sono giorni d'uscita migliori di giorni a caso con lo stesso guadagno
  aperto (mediana placebo 57k $), ma uscire resta peggio che non uscire (70,6k contro 78,5k). Con 6 test, un p di 0,036 non
  regge Holm.
- Vicini (`vicini.csv`): C1 con rA 1,5/2,5, vr 1,5/2,5, ≥ 7%: 50–64k $, tutti sotto W3.2 in IS e OOS. C5 con eA 1,5 / 2:
  77,5k / 79,0k $ con 6 / 4 uscite (CAGR/DD 1,975 / 1,998: pari a W3.2, meglio in OOS e peggio in IS, peggio su ETH 0,80–0,81);
  vr 1,5: 82,6k $ ma DD −22,8% e CAGR/DD 1,90, IS 1,88, 2018–20 0,75. Nessun vicino passa C1. R2 con 3% / 8%: 48–49k $.
  LIM 1,25 / 1,5 / 2,5 ATR: 20,1k / 29,7k / 48,1k $ (DD −34,0 / −29,9 / −21,2%).
- ETH (conferma esterna): C3, C4, C5 sopra W3.2 (0,92–1,09 contro 0,92), C1, C2, C6 sotto. Non confermato su BTC, quindi non conta.

## Parte descrittiva
### 1 · Cascate a favore dentro i trade W3.2 (`eventi_trade.csv`)
Movimento nel verso del trade dall'apertura successiva (> 0 il trend prosegue, < 0 rimbalzo contro la posizione).
| Campione | Def. | Cascate / trade | Media 3 / 7 / 14 g | Prosegue a 3 / 7 / 14 g | Estremo migliore dopo (intra / chiusura) | W3.2 esce meglio dell'apertura successiva |
|---|---|---|---|---|---|---|
| BTC 2021+ | D1 | 14 / 9 | +0,4 / +5,0 / +4,9% | 7 / 10 / 9 su 14 | 13 / 12 su 14 | 5 su 14 (media −4,9%) |
| BTC 2021+ | D3 | 9 / 5 | +3,1 / +2,2 / +1,0% | 7 / 5 / 5 su 9 | 6 / 8 su 9 | 4 su 9 (media −4,0%) |
| BTC 2018–20 | D1 | 7 / 4 | +0,8 / +5,7 / +10,1% | 4 / 5 / 5 su 7 | 6 / 6 su 7 | 5 su 7 (media +6,2%) |
| BTC 2018–20 | D3 | 2 / 2 | −2,9 / +11,8 / +17,5% | 1 / 1 / 2 su 2 | 2 / 2 su 2 | 2 su 2 |
| ETH 2021+ | D1 | 6 / 4 | −1,9 / −1,0 / −0,1% | 2 / 2 / 2 su 6 | 5 / 5 su 6 | 1 su 6 (media −26,4%) |

Lettura: su BTC la cascata a favore non segna la fine del movimento: quasi sempre il trade fa in seguito un estremo migliore.
Dal 2021 però W3.2 esce in media il 4–5% peggio dell'apertura successiva (restituisce, lezione 109); nel 2018–20 il contrario
(+6%). Il vantaggio teorico dell'uscita si perde nel rientro.

### 2 · Il caso del 21/11/2026 (`caso.txt`; fuori campione)
| Giorno | Minimo | Chiusura | Rend. a favore (ATR) | Escursione (ATR) | Volume / media 30 g | Restituito | D1 | D3 | Limite 1,25 / 1,5 / 2 ATR |
|---|---|---|---|---|---|---|---|---|---|
| 20/11 | 57.778 | 58.952 | 1,15 | 1,59 | 2,50 | 24% | no | no | preso a 58.684 / preso a 58.023 / no (56.702) |
| 21/11 | 55.130 | 60.216 | −0,45 | 1,36 | 2,19 | 87% | no | **sì** | preso a 55.450 / no (54.750) / no (53.350) |

- D1 (soglie dell'incarico) **non** riconosce il 21/11: il giorno ha chiuso in rialzo del 2,1%. Lo riconosce solo D3, costruita apposta.
- Uscita eseguibile con D3: apertura del 22/11, **60.276 $** con slippage (non 55.130). Rientro R1: il segnale short è ancora
  vero alla chiusura di domenica 22/11 (61.271 sotto EMA21 74.273, flusso −1,53σ) → nuovo short lunedì 23/11 a 61.210 $,
  esposizione 0,875, stop 78.769 $. R2 (rimbalzo 5% = chiusura ≥ 63.290 $) non ancora scattato in chiusura.
- Il limite a 2 ATR (variante C6) non veniva preso. Quelli a 1,25 e 1,5 ATR venivano presi **il 20/11** a 58,7k / 58,0k $, cioè
  prima del minimo: nessun ordine piazzato in anticipo comprava a 55.130.

Confronto in dollari su 50.000 $ (short 0,744 BTC da 65.286 $), al 23/11 con BTC a 63.850 $ (candela in corso):
| Scelta | P/L | Contro il tenere |
|---|---|---|
| W3.2: tenere | +1.045 $ | — |
| Chiudere al minimo 55.130 (non eseguibile) | +7.560 $ lordi | — |
| D3 tutto + rientro R1 (C5) | +1.632 $ | +587 $ |
| D3 metà | +2.364 $ | +1.319 $ |
| D3 tutto, nessun rientro | +3.683 $ | +2.638 $ |
| Limite 1,5 ATR (preso il 20/11) + R1 | +3.209 $ | +2.164 $ |

In questo caso uscire avrebbe reso di più, finora. È il caso che ha fatto nascere la domanda: non è una prova (lezione 79).

### 3 · Test evento generale: dopo una cascata al ribasso BTC rimbalza? (`eventi_mercato.csv`)
Primo giorno di cascata (pausa 7 g), rendimento dall'apertura successiva; "eccesso" = meno la media di tutti i giorni.
| Evento (ribasso) | Campione | n | Media 3 / 7 / 14 g | Eccesso 7 g | p (7 g) | Positivi a 7 g |
|---|---|---|---|---|---|---|
| D1 in chiusura | BTC 2021+ | 12 | −3,0 / −4,2 / −3,6% | **−4,7** | 0,036 | 3 / 12 |
| | 2021–23 / 2024–26 | 8 / 4 | | −2,9 / −8,3 | 0,35 / 0,012 | 3 / 8, 0 / 4 |
| | BTC 2018–20 · ETH 2021+ | 6 · 7 | | +0,1 · −0,9 | 0,99 · 0,81 | 3 / 6 · 3 / 7 |
| D3 con rifiuto | BTC 2021+ | 12 | +1,7 / +0,3 / +1,4% | −0,3 | 0,89 | 8 / 12 |
| | 2021–23 / 2024–26 | 5 / 7 | | +0,8 / −1,1 | 0,83 / 0,63 | 4 / 5, 4 / 7 |
| | BTC 2018–20 · ETH 2021+ | 4 · 17 | | −7,9 · +1,2 | 0,12 · 0,62 | 2 / 4 · 10 / 17 |

Holm sui 2 test primari: nessuno passa (0,036 > 0,025). Il segno di D1 è l'opposto del rimbalzo (prosecuzione), stesso segno
nelle due metà, nullo nel 2018–20 e su ETH. D3 a 3 giorni +1,5 punti (p 0,30): niente. Speculare al rialzo, D1: +8,4 punti a
7 g (p 0,003, n 8; ETH +7,7, p 0,02; 2018–20 +0,3): momentum, non inversione. Vicini D1: vr 1,5 −6,2 (p 0,003), rA 1,5 −1,9
(p 0,27), ≥ 7% −0,7 (p 0,71): instabile. Coerente con le lezioni 69 e 81: il giorno di crollo non distingue il rimbalzo dalla
prosecuzione, e al più vale il momentum.

## Metodo, limiti, deviazioni
- Motore `cs_engine.py` (copia di tp_engine/radar.weekly con uscite giornaliere, limite, R1/R2/R3, placebo): senza regole
  riproduce W3.2 al centesimo in 5 campioni (78.473,92 $; IS 33.477; OOS 23.488; 2018–20 25.142; ETH 37.575).
- Dati congelati p2_nuovi fino al 15/11; 2018–20 su dati proxy con volume solo spot. Il caso usa i dati del tool fino al 21/11
  più le candele Binance spot del 22 e 23/11 (`dati/btc_1d.json`; il 23/11 è in corso, funding 22–23/11 non incluso).
- Potenza: 13 trade, 5–12 Δ non nulli; con 5 Δ (C5) la permutazione non può scendere sotto 0,031.
- Deviazioni dal PREREG: (1) dopo la prima esecuzione corretto un errore nella sola tabella descrittiva 2018–20 (il trade
  aperto a fine 2020 veniva esteso oltre il periodo: 23 eventi invece di 7); varianti, criteri e placebo non cambiano.
  (2) Nel caso del 21/11 sono riportate, come descrizione, anche combinazioni non preregistrate (D3 metà, D3 senza rientro,
  limite senza rientro). Nessun'altra deviazione.
- Esecuzione: `python3 cs_count.py` (conteggi, prima del PREREG) → `python3 cs_run.py` (~3 min) → `python3 cs_caso.py`.

## Lezione proposta per RESEARCH.md
**Lezione 116**: uscire in profitto nel giorno di "cascata a favore" (movimento giornaliero ≥ 2 ATR con volume ≥ 2× la media, o
crollo con rifiuto tipo 21/11/2026) e rientrare non migliora W3.2: 0/6 varianti passano (PREREG 9e437db); 34–73k $ contro
78,5k, DD uguale o peggiore, ΣΔ per trade sempre negativa, p dei segni 0,63–0,97. Dopo una cascata a favore il trend di solito
prosegue (10 su 14 a 7 giorni, estremo migliore in seguito 13 su 14) e il rientro compra peggio (−5/−14% sui rientri finali).
Il minimo del giorno non è un prezzo eseguibile: l'uscita reale è l'apertura successiva (60.276 $, non 55.130) e un limite
abbastanza vicino da essere preso (1,25–1,5 ATR giornalieri) fa 20–30k $. Test evento: dopo un crollo in chiusura con volume BTC
non rimbalza, a 7 giorni scende ancora (−4,7 punti, 3 positivi su 12, p 0,036 senza Holm; nullo nel 2018–20 e su ETH); dopo un
crollo con rifiuto effetto nullo. Nel caso del 21/11 l'uscita avrebbe reso +0,6/+2,6k $ su 50k: un caso, non una regola. Con le
lezioni 105, 109 e 114: le decisioni giornaliere sulle posizioni settimanali non hanno mai migliorato W3.2; non riproporre
senza dati nuovi (liquidazioni reali multi-borsa, test orario preregistrato).
