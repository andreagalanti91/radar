# Dati nuovi per gli ingressi e le uscite di W3.2 · 27/11/2026 · NESSUNA VARIANTE PASSA

**Verdetto.** Nessuna delle 9 varianti preregistrate (PREREG ba77738) migliora W3.2: W3.2 resta invariata. Scelta finale secondo
la regola: **nessuna**. Lo scanner altcoin non è stato eseguito, perché nessuna variante passa su BTC/ETH.

| # | Variante | Obiettivo | Esito |
|---|---|---|---|
| V1 | COT-A: niente ingressi contro la variazione a 4 report della posizione netta degli asset manager CME | A (evitare perdite) | non passa |
| V2 | COT-B: ingresso aggiuntivo quando il flusso perp è contrario ma il COT conferma | B (più ingressi) | non passa |
| V3 | BASE-A: niente ingressi contro la variazione a 28 g della base Deribit | A | non passa |
| V4 | BASE-B: ingresso aggiuntivo con la base che conferma | B | non passa |
| V5 | FUNDING-A: niente long con funding medio multi-exchange ≥ 90° percentile, niente short ≤ 10° | A | non passa |
| V6 | MINER-A: niente long durante la capitolazione dei miner (hash ribbon) | A | non passa (il più vicino: placebo p 0,042, Holm no) |
| V7 | MINER-E: long anticipato nelle 8 settimane dopo la capitolazione | E (entrare prima) | non passa |
| V8 | FLUSSI-A: niente ingressi contro i flussi netti verso gli exchange a 7 g (CoinMetrics) | A | non passa |
| V9 | SALDO-B: ingresso aggiuntivo con il saldo sugli exchange a 28 g in calo | B | non passa |

## Risultati
10.000 $ a 1x, costi e funding inclusi, partenza da flat, fine 24/11/2026. Le celle riportano: capitale finale $ / DD % /
CAGR/DD, più operazioni (aperta inclusa) / WR delle chiuse %. Insieme = BTC + ETH, 10.000 $ ciascuno dal 11/01/2021.

| Variante | BTC dal 2018 | BTC dal 2021 | ETH dal 2021 | Insieme | OOS 2023→ CAGR/DD BTC · ETH | Placebo p |
|---|---|---|---|---|---|---|
| **W3.2** | **242.755 / −37,3 / 1,16** | **84.820 / −21,1 / 2,07 / 14 / 92,3** | **39.572 / −27,5 / 0,96 / 15 / 57,1** | **124.392 / −20,2 / 1,81** | **1,33 · 0,64** | – |
| V1 COT-A | 46.495 / −35,6 / 0,53 | 26.639 / −26,3 / 0,69 / 13 / 75,0 | 32.665 / −26,2 / 0,85 / 13 / 58,3 | 59.304 / −21,4 / 0,95 | 1,28 · 0,61 | 0,690 |
| V2 COT-B | 185.526 / −41,3 / 0,94 | 52.982 / −27,7 / 1,18 / 21 / 70,0 | 28.931 / −45,3 / 0,44 / 21 / 45,0 | 74.939 / −35,3 / 0,72 | 0,98 · 0,40 | 0,963 |
| V3 BASE-A | 108.810 / −37,3 / 0,83 | 49.680 / −21,1 / 1,48 / 13 / 83,3 | 19.366 / −27,5 / 0,43 / 15 / 50,0 | 69.046 / −20,7 / 1,13 | 1,07 · 0,17 | 0,466 |
| V4 BASE-B | 185.894 / −50,8 / 0,77 | 67.444 / −31,7 / 1,21 / 21 / 75,0 | 26.148 / −51,0 / 0,35 / 23 / 45,5 | 84.713 / −36,9 / 0,76 | 0,99 · 0,39 | 0,857 |
| V5 FUNDING-A | 192.441 / −31,9 / 1,24 | 61.933 / −18,9 / 1,92 / 13 / 83,3 | 31.395 / −27,5 / 0,78 / 13 / 50,0 | 93.328 / −17,7 / 1,69 | 0,95 · 0,42 | 0,686 |
| V6 MINER-A | 220.107 / −37,3 / 1,11 | 76.906 / −21,1 / 1,96 / 14 / 84,6 | 42.418 / −22,9 / 1,22 / 13 / 58,3 | 119.323 / −18,9 / 1,89 | 1,33 · 0,97 | 0,042 |
| V7 MINER-E | 123.362 / −36,2 / 0,90 | 42.695 / −36,2 / 0,77 / 22 / 61,9 | 35.495 / −38,4 / 0,63 / 22 / 47,6 | 72.569 / −34,9 / 0,70 | 0,47 · 0,26 | 0,740 |
| V8 FLUSSI-A | 176.041 / −33,9 / 1,12 | 43.499 / −23,9 / 1,18 / 12 / 75,0 | 18.741 / −36,1 / 0,31 / 13 / 41,7 | 62.240 / −22,4 / 0,95 | 0,95 · 0,07 | 0,472 |
| V9 SALDO-B | 180.673 / −37,3 / 1,03 | 48.762 / −31,7 / 0,97 / 19 / 72,2 | 20.346 / −47,7 / 0,27 / 23 / 45,5 | 69.108 / −34,9 / 0,68 | 0,94 · 0,29 | 0,944 |
| *Buy & hold* | *43.514 / −81,2 / 0,22* | *20.635 / −76,6 / 0,17* | *13.362 / −79,3 / 0,06* | – | – | – |

IS 2018–22 / 2021–22, 2024→ e vicini sono in `fase2_output.txt` e `risultati.csv`.

**Come leggere i risultati:**
- **Filtri A.** Tutti tolgono rendimento su BTC. Bloccare un ingresso di W3.2 spesso non evita la perdita: sposta l'ingresso di
  qualche settimana oppure salta un trend intero. COT-A porta BTC dal 2021 da 84,8k a 26,6k.
- **Il più vicino, MINER-A.** Su ETH migliora (42,4k contro 39,6k, DD −22,9 contro −27,5) perché evita il long del 06/2024
  (−21,4%). Ma salta anche il long del 07/2025 (+15,3%), su BTC peggiora (76,9k) e i vicini non reggono su nessuno dei due
  asset. Placebo p 0,042, sopra la soglia di Holm (0,0056): è l'effetto di un trade solo.
- **Ingressi B/E.** Aggiungono 5–8 operazioni per asset, ma con WR del 45–75% e DD del −28/−51%. Gli ingressi che W3.2 scarta
  perché il flusso perp è contrario sono davvero peggiori. Il flusso resta il filtro che separa, nessuna fonte nuova lo sostituisce.

## Cosa abbiamo imparato dalle 11 perdite e dai movimenti persi (`errori/`)
- **Long persi (8):** 6 sono entrati nelle prime 1–3 settimane del regime. È una caratteristica di prezzo, già vista: metà dei
  long vincenti nasce allo stesso modo.
- **Perdite grandi (BTC 01/2018 −25%, ETH 06/2024 −21%):** sono long in trend vecchi e affollati. Nessuna fonte nuova le isola
  senza togliere vincenti.
- **Short persi (3):** sono stati aperti dopo un crollo, dal 38% al 43% sotto la SMA40. Le fonti nuove non li distinguono meglio
  del prezzo.
- **Uscite tardive (12):** sono il costo noto dei trend lunghi (lezione 109).
- **Movimenti oltre il 30% presi per meno di un terzo:** BTC 12 su 21, ETH 13 su 22. Quasi tutti vanno contro il regime: è la
  scelta di W3.2 di non operare contro il trend, non un errore. Dove il blocco era il flusso perp, sostituirlo con COT, base o
  saldo sugli exchange (V2, V4, V9) dà ingressi perdenti.

## Cosa significa per l'utente
- **Strategia:** W3.2 resta com'è. Le 5 fonti gratuite non migliorano né gli ingressi né la frequenza.
- **Abbonamenti:** pagare non conviene oggi. CryptoQuant Professional (713–1.188 $ l'anno, `COSTI-ABBONAMENTI.md`) darebbe
  soprattutto flussi verso gli exchange e on-chain più fini. La versione gratuita di questi flussi (CoinMetrics) è la peggiore
  del test (V8, V9) anche come limite superiore. Coinglass (273–420 $) darebbe OI e funding aggregati: il funding medio di 3
  borse (V5) non passa, e l'OI era già fra i dati osservati nelle perdite senza separarle. Prima di pagare servirebbe un'ipotesi
  nuova, non la stessa informazione più fine.
- **Contesto:** i dati scaricati possono restare come contesto in dashboard (base, COT, hash ribbon), senza valore di segnale.

## Limiti
- **Pochi trade:** 14 su BTC dal 2021, 15 su ETH. Le varianti cambiano da 1 a 10 trade: i risultati sono fragili in entrambe le
  direzioni.
- **Flussi CoinMetrics:** sono "flash" e ricalcolati anche nel passato. Il loro risultato è un limite superiore, e anche così
  non passa.
- **Fonti corte:** COT ETH dal 04/2021, base BTC dal 08/2018, Hyperliquid dal 2023. OKX e Bitget non hanno storico gratuito,
  Bybit e BitMEX sono bloccati. Le date del COT durante gli shutdown sono approssimate per prudenza.
- **Analisi degli errori vista prima:** ho analizzato le perdite prima di scrivere le definizioni (rischio dichiarato nel
  PREREG). Le definizioni sono da manuale e uguali per tutti gli asset.

## Lezione 132 proposta
**Lezione 132**: fonti nuove gratuite per gli ingressi di W3.2 (research/dati_nuovi, PREREG ba77738, 9 varianti, Holm m = 9):
nessuna passa. Le fonti provate sono COT CFTC degli asset manager CME, base dei future Deribit, funding medio Binance/Deribit/
Hyperliquid, hash ribbon dei miner, flussi e saldo sugli exchange CoinMetrics.
- **Filtri d'ingresso (A):** costano su BTC (COT-A 26,6k, base 49,7k, funding 61,9k contro 84,8k): bloccare un ingresso di W3.2
  sposta o salta il trend invece di evitare la perdita. MINER-A migliora solo ETH grazie a un trade (06/2024), placebo p 0,042,
  vicini incoerenti.
- **Ingressi aggiuntivi o anticipati (B/E):** al posto del flusso perp contrario aggiungono 5–8 operazioni con WR del 45–75% e
  DD fino a −51%. Il flusso perp resta l'unica informazione che separa (conferma delle lezioni 86 e 97).
- **Analisi delle 11 perdite:** le perdite vengono da long al cambio di regime, long in trend affollati e short dopo un crollo:
  caratteristiche di prezzo e di leva che nessuna fonte nuova isola.
- **Movimenti persi:** sono quasi tutti contro il regime, per scelta.
- **Abbonamenti:** nessun abbonamento (CryptoQuant, Coinglass) giustificato senza un'ipotesi nuova. I flussi exchange
  CoinMetrics sono "flash" (non point-in-time): limite superiore.

## File
`PREREG.md`, `DEVIAZIONI.md`, `fetch.py` (scarico), `fonti.py` (segnali), `motore.py` (W3.2 + una regola; verifica 84.820 /
242.755 / 39.572 $), `errori.py` e `errori/` (analisi degli errori), `conteggi.py` e `conteggi_output.txt`, `fase2.py`,
`fase2_output.txt`, `risultati.csv`, `data/`.
