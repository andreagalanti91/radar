# Order book e liquidazioni come supporto a W3.1 · 22/11/2026 · INDICATIVO, nessuna regola

**Verdetto: oggi né il book né le liquidazioni danno supporto misurabile alla strategia.** Su 15 giorni di dati nessuna delle
celle preregistrate supera le soglie; l'unico segnale vicino (squilibrio ±1% → 1 ora) è più piccolo dei costi e riguarda
un orizzonte che W3 (settimanale) non usa. Metodo e soglie: PREREG.md (scritto prima dei risultati; va committato da solo e prima
dei risultati, poi il resto). Script: bl_data.py, bl_run.py; output: risultati.txt, h1_squilibrio.csv, h2_muri.csv,
h2_episodi.csv, h3_confluenza.csv, h3_episodi.csv, h4_giorni.csv.

## Dati disponibili
- data/orderbook.csv: dal **07/11/2026 08:53 UTC**, 274 foto (≈ 8 al giorno fino al 13/11, orarie dal 14/11). Colonne: profondità
  e squilibrio aggregati di 5 exchange a ±0,25/0,5/1/2%, un solo muro per lato (fascia 0,05% più grande fra 0,1% e 2%), spread,
  microprezzo. **Manca ±3%**; a ±2% coprono entrambi i lati in media 1,9 fonti su 5. Il book grezzo non è salvato.
- Liquidazioni reali: data/liquidations.csv (OKX dal 30/10), data/liq_events (OKX, Gate, dYdX… dal 10–11/11; senza Binance e Bybit).
- On-chain (Hyperliquid, Lighter): dal 11/11. Mappa stimata: ricostruita ora per ora con radar/liqmap.build (504 ore prima di t).

## Risultati (n = foto; "indip." = osservazioni indipendenti stimate)
| Cella | n (indip.) | Effetto | IC 95% | p | Esito |
|---|---|---|---|---|---|
| H1a imb ±1% → 1h | 273 (273) | ρ +0,14; Q5−Q1 +0,23% | +0,02 / +0,28 | 0,031 | no: sotto i costi (0,30%) e oltre Bonferroni (0,008) |
| H1a imb ±1% → 4h | 269 (~96) | ρ +0,11 | −0,06 / +0,30 | 0,27 | no |
| H1a imb ±1% → 24h | 248 (~15) | ρ +0,08 | −0,10 / +0,31 | 0,32 | no |
| H1b imb ±2% → 1h / 4h / 24h | 273 / 269 / 248 | ρ +0,06 / +0,02 / −0,20 | tutti includono 0 | 0,32 / 0,84 / 0,25 | no |
| Muro ask/bid (screenshot, non prereg.) → 1/4/24h | 273 / 269 / 248 | ρ −0,08 / −0,10 / −0,02 | includono 0 | ≥ 0,18 | no |
| H2 muro ≥ 3×, ≥ 0,3%: raggiunto | 24 episodi | 75% contro 73% casuale | 55–88% | 1,00 | no |
| H2 superato / rimbalzo | 24 | 62,5% vs 65%; 21% vs 16% | 43–79%; 9–40% | 0,83; 0,57 | no |
| H2 solo bid / solo ask (rimbalzo) | 14 / 10 | 21% vs 15%; 20% vs 17% | 8–48%; 6–51% | 0,70; 1,00 | no |
| H3a muro + fascia stimata (rimbalzo) | 6 | 33% vs 14% | 10–70% | 0,21 | no (n troppo piccolo) |
| H3b muro + on-chain | 1 | — | — | — | non giudicabile |
| H3c muro + S/R (rimbalzo) | 19 | 21% vs 16% | 9–43% | 0,76 | no |

Parametri vicini di H2 (2,5×/4×, distanza 0,2%/0,5%): 1 cella su 12 sotto p 0,05 (d ≥ 0,2%: muri raggiunti 73% contro 85%
casuale, cioè meno spesso): atteso per caso fra 12 prove, segno opposto all'idea "il muro attira".
Controlli: lo squilibrio è legato al passato più che al futuro (ρ con il rendimento delle 24 ore precedenti −0,29 a ±1% e −0,48
a ±2%: dopo una discesa il book aggregato è più pieno sui bid). Il rapporto muri ask/bid aggregato non ha mai superato 2,5× (mediana
0,94): lo 3–4× dello screenshot è una lettura di una sola piattaforma, non del mercato aggregato. Le zone S/R del tool sono larghe
(~1,8 ATR + 0,5%): contengono 19 muri su 24, quindi non discriminano.

## H4 · giorni chiave (descrittivo; tabella completa in h4_giorni.csv)
- 13/11 cascata (71,5k → 67,6k): liquidazioni reali long 120 M$ contro 14 M$ short; squilibrio ±1% +0,09 (book più pieno sui bid)
  mentre il prezzo scendeva: il book non ha anticipato nulla.
- 15/11 squeeze (62,0k → 66,1k): short liquidati 36,5 M$ ≈ long 33 M$; squilibrio leggermente negativo (−0,03).
- 16–22/11 short W3.1 (ingresso 65.286): 20/11 picco di liquidazioni long (160 M$) con squilibrio ±2% +0,47 (bid molto più pesanti)
  e prezzo a 57,8k; 21/11 minimo 55,1k e rimbalzo con 78 M$ di short liquidati. Un book "pieno sotto" non ha fermato la discesa.
  Short a 60,8k: +7,5% sul prezzo, ~+2,9% lordo sul capitale (esposizione 0,389). Buy & hold dal 07/11: −20,2%.
- La tabella standard 10.000 $ dal 2021 (rendimento, DD, MAR) non è applicabile: il book esiste da 15 giorni e non c'è una regola.

## Potenza: quanto storico servirebbe (α 0,05, potenza 80%)
| Effetto | Osservazioni indipendenti | Foto orarie |
|---|---|---|
| ρ = 0,10 a 1h / 4h / 24h | 783 | ~33 / ~130 / ~780 giorni |
| ρ = 0,05 a 1h | 3.137 | ~130 giorni |
| H2: +10 punti su base 50% | ~194 episodi | ~120 giorni (1,6 episodi al giorno) |

Sull'orizzonte di W3 (settimane) servirebbero anni: il book può servire al più a scegliere l'ora di esecuzione del lunedì.

## Cosa registrare per il test in avanti
1. Squilibrio a ±3% e ±5% e per singolo exchange (soprattutto i perp: oggi c'è solo OKX perp); fotografie ogni 15 minuti.
2. I 5 muri più grandi per lato (prezzo, $, exchange) invece di uno solo, e la loro durata fra una foto e l'altra (muri tolti).
3. Mappa stimata: conservare il riassunto orario oltre le 31 ore di liqmap_prev.json.
4. Liquidazioni Binance/Bybit (raccoglitore liqstream) per avere il lato reale delle cascate.

Rifare: H1 a 1 ora verso il 20/12/2026 (~800 foto orarie); H2/H3 non prima di marzo 2027; sempre con questa preregistrazione.

## Lezione proposta per RESEARCH.md
**Lezione 105** (proposta): order book aggregato (5 exchange, ±1/±2%) e muri, da soli o in confluenza con liquidazioni stimate,
livelli on-chain e S/R, non mostrano vantaggio in 15 giorni di dati (07–22/11/2026, studio indicativo): squilibrio → 1h ρ +0,14
(p 0,03) ma sotto i costi, nulla a 4–24h; i muri vengono raggiunti, superati e respinti come livelli casuali alla stessa distanza
(24 episodi). Lo squilibrio segue il rendimento passato (dopo un calo il book è pieno sui bid) e non ha fermato la cascata del 13/11
né la discesa del 20/11. Un rapporto ask/bid di 3–4× visto su una heatmap non compare nel book aggregato (massimo 2,5×). Il book resta
contesto; un test vero richiede ~1 mese di foto orarie per l'ora successiva e mesi per i muri, mai per l'orizzonte di W3.

> Nota di processo (22/11): PREREG.md e risultati sono stati scritti nella stessa fase e committati insieme: l'ordine non è provabile con git (errore di orchestrazione della sessione principale). Lo studio è indicativo e non produce regole.
