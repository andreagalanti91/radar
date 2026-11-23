# Forza giornaliera: chi compra (spot contro perp), livelli chiave, uso su W3.2 · BTC (+ ETH) · 23/11/2026

**Verdetto: non regge. Nessuna ipotesi e nessuna variante passa; W3.2 resta invariata, nessuna modifica a radar/.**
- **H1 "squeeze a leva"**: nessun effetto. Su BTC i rialzi guidati dai perp rendono a 7 giorni PIÙ di quelli guidati dallo spot
  (+1,3 punti, p 0,55): segno opposto alla tesi del trader. Su ETH il segno è quello atteso (−2,8, p 0,27) ma non significativo.
- **H1 speculare "flush a leva"**: nessun effetto (+1,4 punti, p 0,51; ETH segno opposto).
- **H2 "spot che guida"**: nessun effetto (0,0 punti sulla media, p 1,00).
- **H3 livello + spot**: nessun effetto, segno opposto: le rotture confermate dallo spot rendono MENO (20 giorni −2,7 punti,
  p 0,23; swing settimanali −2,9, p 0,085; uguale su ETH per i 20 giorni).
- **E-in (ingresso quando perp e spot concordano)**: peggiora, 62–65k $ contro 78k (lezione 105 confermata).
- **E-in4 (limite sul livello)**: peggiora, 71,6k $; limite eseguito 1 volta su 13.
- **E-out (uscita su rottura guidata dallo spot)**: peggiora, 64–74k $, DD uguale o più alto; il placebo non la distingue da
  uscite in giorni a caso (p 0,25–0,72).
- **E-hold**: i movimenti contrari "solo perp" non finiscono meglio di quelli "con spot" (tabella sotto).
- **Regola "flip" dei livelli (addendum, esplorativa)**: short alla perdita del livello 10.000 → 5.145 $ (112 trade, WR 23%).
Preregistrazione: `PREREG.md` commit **32bcbba** (da solo, prima di ogni rendimento; conteggi in `conteggi.txt`);
`ADDENDUM.md` commit **73583f7** (da solo, prima di eseguire la parte "flip", dichiarata esplorativa).

## Conviene controllare ogni giorno la forza per entrare o uscire?
**No.** Con questi dati (Binance spot e perp giornalieri dal 2021) sapere chi guida un movimento non dice cosa farà il prezzo nei
3–14 giorni successivi, né su BTC né su ETH, e usarlo per ritardare l'ingresso o anticipare l'uscita di W3.2 costa 4–16k $ senza
ridurre il drawdown. Il controllo giornaliero utile resta quello già in uso: trailing a 2,5 ATR settimanali e decisione della
domenica. Limite onesto: con 13 trade il test sulle varianti ha poca potenza ("nessun miglioramento dimostrabile", non
"impossibile"); i test evento invece hanno 32–51 eventi per classe e l'effetto ha il segno sbagliato o è nullo.

## Test evento (BTC, 01/01/2021 → 15/11/2026; rendimento a 7 giorni; media di tutti i giorni +0,55%)
Evento: primo giorno con movimento ≥ 5% dal minimo/massimo di 3 giorni (pausa 7 g). Classe: perp o spot spinge di più
(z a 180 giorni dei flussi a 3 giorni, differenza ≥ 0,5).
| Test | Confronto | n | Effetto 7 g | p | Metà 21–23 / 24→ | Atteso | ETH (effetto, p) | Esito |
|---|---|---|---|---|---|---|---|---|
| T1 squeeze a leva | rialzi perp − spot | 50 / 37 | **+1,28** | 0,55 | +1,97 / +0,18 | < 0 | −2,77 (0,27) | nessun effetto |
| T2 flush a leva | ribassi perp − spot | 51 / 32 | +1,37 | 0,51 | +1,99 / +0,44 | > 0 | −0,60 (0,76) | nessun effetto |
| T3 spot che guida | rialzi spot − media | 37 | 0,00 | 1,00 | +0,09 / −0,10 | > 0 | +1,65 (0,27) | nessun effetto |
| T4 rottura 20 g | spot − perp, nel verso | 35 / 35 | **−2,72** | 0,23 | −2,48 / −3,06 | > 0 | −3,58 (0,12) | nessun effetto (segno opposto) |
| T5 rottura swing settimanale | spot − perp, nel verso | 53 / 51 | **−2,89** | 0,085 | −4,97 / −0,79 | > 0 | +1,15 (0,49) | nessun effetto (segno opposto) |

Rendimento medio a 7 g per classe (BTC): rialzi perp +1,82% · spot +0,54% · misti +0,52%; ribassi perp +0,68% · spot −0,69% ·
misti +1,90%. A 3 e 14 giorni stessi segni, p 0,27–0,96 (`risultati.txt`, `eventi.csv`). Holm su 13 test: tutti 1,00.
Vicini (`vicini.csv`): T1 ha segno "sbagliato" in 5 su 6 (N 2/3, X 4/5/6%, D0 1, versione in dollari del trader: +0,6/+2,0
punti; solo N 5: −1,1). T2 positivo in 5 su 6 ma mai significativo e negativo su ETH. Nessun risultato a favore della tesi.
Lettura: su BTC dal 2021 i rimbalzi partiti dai perp non sono "finiti in fretta" più degli altri; le rotture con lo spot
dietro sono spesso l'ultimo tratto del movimento (chi compra spot compra tardi).

## Uso su W3.2 (10.000 $, 1x, costi W3.2; IS e OOS ripartono da 10.000 $)
| Variante | Finale 2021+ | DD | CAGR/DD | Trade | WR | IS fin. / CDD | OOS fin. / CDD | 2018–20 fin. / CDD | ΣΔ log (senza 2) | p segni | p placebo | ETH finale / CDD |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| **W3.2 (in uso)** | **78.474** | −21,1 | 1,990 | 13 | 92,3 | 33.477 / 2,574 | 23.488 / 1,639 | 25.142 / 0,966 | — | — | — | 37.575 / 0,919 |
| Buy & hold | 22.549 | −76,6 | 0,194 | — | — | 14.590 | 15.425 | 21.046 | — | — | — | — |
| E-in1 flussi concordi 1 g, K 3 | 65.427 | −20,9 | 1,802 | 13 | 84,6 | 28.792 / 2,023 | 22.770 / 1,661 | 24.611 / 0,913 | −18,2 (−20,6) | 0,99 | 0,22 | 37.293 / 0,819 |
| E-in2 come sopra, K 5 | 62.101 | −23,8 | 1,531 | 13 | 84,6 | 27.184 / 1,662 | 22.890 / 1,701 | 23.444 / 0,800 | −23,4 (−24,8) | 0,99 | 0,47 | 36.683 / 0,807 |
| E-in3 flussi 3 g, K 5 | 64.428 | −24,0 | 1,558 | 13 | 84,6 | 28.908 / 1,775 | 22.332 / 1,462 | 22.439 / 0,753 | −19,7 (−20,1) | 0,99 | 0,36 | 42.091 / 1,075 |
| E-in4 limite sul livello swing | 71.579 | −21,1 | 1,885 | 13 | 92,3 | 32.968 / 2,385 | 21.755 / 1,471 | 22.988 / 0,794 | −9,2 (−9,5) | 0,94 | 0,30 | 33.292 / 0,826 |
| E-out1 tutto, rottura 20 g da spot | 70.828 | −22,3 | 1,772 | 13 | 92,3 | 30.350 / 2,275 | 23.384 / 1,540 | = W3.2 | −10,3 (−16,8) | 0,84 | 0,58 | 37.286 / 0,936 |
| E-out2 metà, come sopra | 74.382 | −21,3 | 1,916 | 13 | 92,3 | 31.901 / 2,450 | 23.363 / 1,616 | = W3.2 | −5,4 (−8,7) | 0,81 | 0,40 | 37.487 / 0,969 |
| E-out3 tutto, rottura 10 g da spot | 64.343 | −25,8 | 1,447 | 13 | 84,6 | 28.917 / 1,650 | 22.295 / 1,421 | 23.709 / 0,864 | −19,9 (−26,4) | 0,84 | 0,72 | 33.150 / 0,679 |
| E-out4 tutto, rottura 20 g "con spot" | 66.494 | −22,6 | 1,689 | 13 | 92,3 | 30.735 / 2,059 | 21.678 / 1,371 | = W3.2 | −16,6 (−26,9) | 0,86 | 0,25 | 33.760 / 0,778 |
| Controllo: ogni rottura a 20 g | 46.803 | −35,4 | 0,849 | 13 | 84,6 | 28.982 / 2,161 | 16.181 / 0,515 | 24.316 / 0,920 | −51,7 | 0,97 | — | 39.535 / 0,966 |

Criteri: C1 (IS e OOS migliori) 0/8 · C2 0/8 migliori (3 uguali perché la regola non scatta) · C3 e C4 tutte · C5 0/8 (ΣΔ già
negativa) · C6 0/8 · C7 0/8. **0 varianti su 8 passano.** ETH: 3 su 8 leggermente sopra (E-in3, E-out1, E-out2), non confermate su BTC.
Cosa succede nei trade (`risultati.txt`, `trade_delta.csv`):
- **E-in**: 7–11 ingressi su 13 ritardati di 1–5 giorni, quasi sempre a un prezzo peggiore (2023-10: 33.103 invece di 30.022;
  2025-11 short: 93.337 invece di 90.270). Aspettare che perp e spot "concordino" significa comprare dopo che il prezzo è già
  partito. Un ritardo a caso della stessa durata fa lo stesso (placebo p 0,22–0,47).
- **E-out**: 8 uscite in 5 trade (E-out1). Si esce sulla rottura e si rientra il lunedì a un prezzo quasi sempre peggiore
  (2023-06: fuori a 25.103, dentro a 26.366; 2025-09: fuori a 108.886, dentro a 112.276). Guardare il flusso aiuta rispetto a
  uscire su ogni rottura (46,8k $), ma solo perché si esce meno volte: uscite a caso nello stesso numero fanno uguale o meglio.
- **2018–20**: flussi spot/perp solo dal 2020, quindi il criterio è quasi vuoto (dichiarato nel PREREG).

## E-hold: i movimenti contrari ≥ 5% in 3 giorni dentro i trade W3.2 (`hold.csv`)
| Asset · chi guida il movimento contrario | n | 7 g dopo, nel verso del trade | Positivi a 7 g | Poi nuovo estremo a favore |
|---|---|---|---|---|
| BTC · solo perp (lo "squeeze") | 35 | +0,5% | 46% | 51% |
| BTC · spot | 14 | +0,9% | 57% | 71% |
| BTC · misto | 24 | +2,7% | 50% | 58% |
| ETH · solo perp | 35 | +1,1% | 43% | 51% |
| ETH · spot | 6 | +4,9% | 67% | 83% |
| ETH · misto | 35 | +0,0% | 57% | 54% |

In 13 trade BTC ci sono stati 73 movimenti contrari ≥ 5%: 12 trade su 13 hanno chiuso in guadagno comunque. Un rimbalzo "solo
perp" contro la posizione non è rientrato più spesso di uno "con spot" (anzi, un po' meno): la distinzione non aiuta a decidere
se tenere. La risposta al rimbalzo 55k → 61k è quella di W3.2: si tiene finché il trailing regge.

## Il caso del 21–23/11 con i nostri dati (`oggi.txt`)
- **I numeri del trader si riproducono nel segno e nell'ordine di grandezza.** Binance, orario, dal minimo (55.130 $, 21/11
  06:00 UTC) a fine 22/11: perp **+626 M$**, spot **−21 M$** (lo spot ha venduto). Solo il 22/11: perp +258 M$, spot +19 M$
  (14:1; rapporto normale dei volumi 9,0). Contratti OKX (provvisorio, altra borsa): +516 M$ dal minimo, +98 M$ il 23/11 fino
  alle 13 UTC, con spot Binance +2 M$. Binance + OKX perp dal 22/11 ≈ +590 M$ contro spot ≈ +21 M$: compatibile con "+880 M$
  contro +23 M$" su più borse. Massimo dopo il minimo 61.960 $ (23/11 03:00), sotto 62,5k.
- **Stato secondo le regole preregistrate (chiusura 22/11)**: rimbalzo +11,1% dal minimo di 3 giorni → evento "rialzo"; classe
  **"misto"** con la finestra primaria a 3 giorni (pz3 −0,25, sz3 −1,27: la finestra contiene ancora le vendite del 20–21/11).
  Con le finestre vicine a 1 e 2 giorni la classe è **"perp"** (pz1 +0,78 / sz1 +0,23; pz2 +0,34 / sz2 −0,81). Descrizione
  corretta: rimbalzo spinto dai perp, spot assente.
- **Cosa dice lo storico di un caso così**: nulla di utile. I 50 rialzi "perp" dal 2021 hanno reso +1,8% a 7 giorni (media
  +0,55%); il rimbalzo può proseguire o no con la stessa probabilità degli altri.
- **W3.2**: short dal 16/11 a 65.286 $, P/L +5,9% alla chiusura del 22/11, trailing 75.764 $; nessuna decisione in sospeso.
  Massimo a 20 giorni 81.196 $: nessuna rottura contraria.
- **ETH**: minimo 1.538 $ (21/11), 1.724 $ il 22/11 (+12,1% dal minimo); dal minimo perp Binance +298 M$, spot −25 M$; classe
  "misto" (pz3 −0,64, sz3 −0,62). W3.2 ETH short dal 09/11 a 2.125 $, P/L +15,2%, trailing 2.311 $.

## Livelli "flip" del trader (addendum, esplorativo: `flip.txt`, `flip_trade.csv`)
- **I livelli coincidono in parte con quelli oggettivi.** Al 07/10/2026 (prima della discesa): 81,4k → swing settimanale 80.600
  (−1,0%) e zona `radar/levels` 80.600–84.450; 74,4k → swing 74.508 (+0,1%) e zona 71.997–74.968; 60,3k → swing 60.000
  (−0,5%); 62,5k → nessuno swing settimanale (il più vicino è 60.000), ma dentro la zona `radar/levels` 61.844–65.000; 48k → nessun
  livello swing attivo (zona `radar/levels` 45.821–49.000 solo dopo la discesa). Quindi 81,4k, 74,4k e 60,3k sono livelli che il
  tool già disegna; 62,5k è una lettura del trader dentro una zona larga.
- **W3.2 contro la sua chiamata**: quando 81,4k è stato perso (22–29/10) W3.2 era LONG (dal 24/08 a 77.812 $); è uscita il 09/11
  a 74.777 $ (−4,1%) ed è entrata short il 16/11 a 65.286 $, cioè il 20% più in basso del trader. Su questo caso il trader ha
  fatto meglio.
- **La regola meccanica su tutti i casi**: "short alla chiusura sotto il supporto, stop sopra il livello, obiettivo il livello
  successivo" dal 2021 fa 10.000 → **5.145 $** (DD −70%, 112 trade, WR 23%, PF 0,82; 2021–23 7.656 $, 2024→ 6.720 $). Sul
  ritest respinto: 6.327 $ (64 trade, WR 30%). Nel calo di ottobre la regola ha shortato 81,6–81,8k quattro volte ed è stata
  fermata tre volte (−2,3/−2,6%) prima dei due trade buoni (+5,9% e +11,9%): il caso riuscito esiste, ma è 1 su 4–5.
- **Con la conferma dello spot non migliora**: perdita del livello con vendita guidata dallo spot −1,07% per trade (29 trade)
  contro −0,80% dei "perp" e +0,14% dei misti (p 0,48). Uscire dai long di W3.2 alla perdita del livello: 37.269 $ (DD −38,9%);
  solo se guidata dallo spot: 49.298 $ (DD −28,8%).
- Conferma le lezioni 75–77 e 106: i livelli descrivono dove il prezzo reagisce, ma operare su ogni rottura perde. Chi ricorda i
  livelli riusciti (81,4k) non conta le rotture false.

## Cosa mostrare in dashboard (solo contesto, mai segnale)
Una riga nel riquadro Contesto, calcolata sull'ultimo giorno chiuso:
"**Ultimi 3 giorni: +11% dal minimo. Chi ha comprato: soprattutto perp (leva), spot quasi assente.**" con le varianti "soprattutto
spot" / "perp e spot insieme", i due netti in M$ (Binance) e la nota fissa: "*Descrizione, non previsione: dal 2021 i rimbalzi
guidati dai perp non sono andati peggio di quelli guidati dallo spot (lezione 114). Non cambia la posizione W3.2.*"
Da non mostrare: probabilità, frecce, "squeeze destinato a finire", livelli "che contano" come trigger.

## Limiti
- Solo Binance (spot e perp USDT-M): niente Coinbase, Bybit, OKX nello storico; il trader probabilmente aggrega più borse. Un CVD
  multi-borsa potrebbe dare classi diverse (stessa riserva della lezione su flusso_trader).
- Barre giornaliere UTC: uno squeeze di poche ore dentro una giornata di vendite finisce in "misto" (è successo il 21–22/11).
  Un test orario (taker_1h dal 2022) non è stato fatto: sarebbe una nuova preregistrazione.
- Liquidazioni: non testate. Dati reali solo Binance COIN-M 06/2023 → 10/2024 e registro dal 10/11/2026 (< 10% del mercato);
  le mappe stimate sono già state escluse come ingressi (lezioni 92, 93) e come segnale orario (108).
- Potenza: 13 trade W3.2; p minimo raggiungibile con 5–11 trade modificati 0,03–0,0005, contro una soglia di Holm di 0,004.
- ETH su dati del tool (37.575 $ al 15/11; in w32_multi 34.760 $ al 10/11).

## Deviazioni dal PREREG
1. `fg_engine.py`, `fg_run.py`, `fg_oggi.py` scritti dopo il commit del PREREG (regole invariate); il motore riproduce W3.2 al
   centesimo in 4 periodi e in 3 configurazioni degeneri, e ETH (37.574,96 $).
2. T3: le due metà sono calcolate contro la media della rispettiva metà.
3. Placebo E-out: le uscite casuali che cadono mentre si è già fuori non vengono ripetute (numero di uscite ≤ variante).
4. Caso 21–23/11: aggiunte le finestre a 1 e 2 giorni nella descrizione (la classe primaria resta quella a 3 giorni).
5. Addendum "flip": scritto dopo i risultati del PREREG, quindi esplorativo; livelli confrontati alla data fissa 07/10/2026.
6. Vicini di T4/T5 limitati a L = 10 (descrittivo). Nessuna revisione critica separata.

## File
PREREG.md · ADDENDUM.md · fg_lib.py · fg_count.py → conteggi.txt · fg_engine.py · fg_run.py (~3 min) → risultati.txt, eventi.csv,
vicini.csv, varianti.csv, trade_delta.csv, hold.csv · fg_oggi.py → oggi.txt, dati/ · fg_flip.py → flip.txt, flip_trade.csv.

## Lezione proposta per RESEARCH.md
**Lezione 114**: guardare ogni giorno "chi compra" (spot contro perp) e i livelli chiave non migliora W3.2 e non prevede il
prezzo. Su BTC dal 2021 (Binance, eventi ≥ 5% in 3 giorni, 32–51 per classe) i rialzi guidati dai perp rendono a 7 giorni +1,3
punti PIÙ di quelli guidati dallo spot (p 0,55; atteso il contrario), i rialzi "spot" valgono la media (0,0), le rotture a 20
giorni e dei livelli swing confermate dallo spot rendono 2,7–2,9 punti MENO (p 0,23 / 0,085); su ETH segni incoerenti, niente
di significativo; Holm su 13 test tutti 1,00. Su W3.2 0/8 varianti passano (PREREG 32bcbba): aspettare che perp e spot
concordino per entrare costa 13–16k $ (62–65k contro 78,5k, come un ritardo a caso), il limite sul livello 7k (eseguito 1 volta su
13), l'uscita sulla rottura guidata dallo spot con rientro il lunedì 4–14k senza ridurre il DD (placebo p 0,25–0,72). Dentro i
trade W3.2 i 35 movimenti contrari "solo perp" non sono rientrati più spesso dei 14 "con spot". La regola "flip" (short alla
perdita del supporto, obiettivo il livello successivo; esplorativa) fa 10k → 5,1k in 112 trade, e la conferma spot non la
salva: i livelli del trader (81,4k, 74,4k, 60,3k) coincidono con quelli del tool, ma la chiamata riuscita è 1 rottura su 4–5.
Il caso del 21–23/11 si riproduce (perp +626 M$, spot −21 M$ dal minimo, Binance) ma non ha valore previsionale. In dashboard
solo come descrizione ("rimbalzo guidato dai perp / dallo spot") con avvertenza. Non riproporre senza dati nuovi: CVD
multi-borsa o test orario preregistrato. research/forza_giornaliera/README.md.
