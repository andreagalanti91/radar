# Validazione della superficie di volatilità (opzioni BTC, Deribit)

Generato da `dati/valida.py` il 2026-11-24 su `superficie.csv.gz` (297666 righe, 3249 giorni,
2018-01-01 → 2026-11-23). Ricostruire: `python3 scarica.py scambi 2018-01-01 AAAA-MM-GG`,
`python3 scarica.py dvol`, `python3 costruisci.py`, `python3 valida.py` (dentro `dati/`).

## Campione e controlli di qualità
Per ogni giorno UTC al massimo 3 pagine da 1000 scambi (dalle 00:00, 08:00 e 16:00 UTC); nei giorni poco liquidi una
pagina copre l'intera giornata.

Giorni in cache: 3249 su 3249 attesi; giorni senza scambi validi: 0. Giorni con campione dell'intera giornata: 913. Indice Deribit vs data/spot.csv (Binance, metà fra apertura e chiusura, dal 2019-09-01): scarto mediano -0.02%, mediana assoluta 0.50%; giorni con indice fuori dal minimo/massimo Binance (±1%): 0.

| anno | giorni | scambi validi per giorno (mediana) | giorni con campione intero |
|---|---|---|---|
| 2018 | 365 | 409 | 363 |
| 2019 | 365 | 971 | 346 |
| 2020 | 366 | 2607 | 168 |
| 2021 | 365 | 2995 | 4 |
| 2022 | 365 | 2996 | 13 |
| 2023 | 365 | 2998 | 4 |
| 2024 | 366 | 2998 | 0 |
| 2025 | 365 | 2997 | 0 |
| 2026 | 327 | 2995 | 15 |

## (a) Copertura per anno
Per ogni giorno: scadenza = venerdì scambiato (in D o nei 3 giorni prima) più vicino a 14/30/60/90 giorni, come farà il
motore (nel 2018–2019 le scadenze erano poche: vedi la distanza mediana sotto); strike alla pari (call, K = spot), +10% (call, ln K/F = +0,10), −10% (put, ln K/F = −0,10).
Percentuale dei giorni di calendario con qualità **"scambi"** (scadenza scambiata quel giorno nel campione, stesso tipo,
una fascia con scambi a moneyness media entro 0,05 da quella richiesta):

| anno | giorni | 14g 0 | 14g +10 | 14g -10 | 30g 0 | 30g +10 | 30g -10 | 60g 0 | 60g +10 | 60g -10 | 90g 0 | 90g +10 | 90g -10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2018 | 365 | 99% | 99% | 97% | 95% | 98% | 93% | 90% | 91% | 84% | 76% | 81% | 76% |
| 2019 | 365 | 100% | 100% | 100% | 98% | 99% | 100% | 94% | 96% | 94% | 87% | 91% | 84% |
| 2020 | 366 | 100% | 100% | 100% | 100% | 99% | 100% | 98% | 98% | 96% | 89% | 86% | 89% |
| 2021 | 365 | 99% | 100% | 100% | 98% | 100% | 99% | 90% | 93% | 93% | 78% | 87% | 85% |
| 2022 | 365 | 99% | 100% | 100% | 100% | 100% | 100% | 92% | 95% | 94% | 82% | 83% | 84% |
| 2023 | 365 | 100% | 100% | 100% | 100% | 100% | 100% | 97% | 99% | 99% | 91% | 95% | 93% |
| 2024 | 366 | 100% | 100% | 100% | 99% | 100% | 100% | 97% | 99% | 98% | 85% | 89% | 87% |
| 2025 | 365 | 100% | 100% | 100% | 99% | 100% | 100% | 98% | 100% | 99% | 95% | 99% | 97% |
| 2026 | 327 | 100% | 100% | 100% | 100% | 100% | 100% | 99% | 100% | 99% | 96% | 98% | 96% |
| tutto | 3249 | 100% | 100% | 100% | 99% | 100% | 99% | 95% | 97% | 95% | 86% | 90% | 88% |

Percentuale dei giorni con un valore qualsiasi (scambi + interpolata + estesa; il resto è "mancante"):

| anno | 14g 0 | 14g +10 | 14g -10 | 30g 0 | 30g +10 | 30g -10 | 60g 0 | 60g +10 | 60g -10 | 90g 0 | 90g +10 | 90g -10 |
|---|---|---|---|---|---|---|---|---|---|---|---|---|
| 2018 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2019 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2020 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2021 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2022 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2023 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2024 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2025 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |
| 2026 | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% | 100% |

Distanza mediana (giorni) fra la scadenza scelta e D+N:

| anno | 14g | 30g | 60g | 90g |
|---|---|---|---|---|
| 2018 | 7 | 8 | 16 | 23 |
| 2019 | 3 | 8 | 13 | 22 |
| 2020 | 2 | 8 | 9 | 18 |
| 2021 | 2 | 8 | 8 | 10 |
| 2022 | 2 | 8 | 8 | 11 |
| 2023 | 2 | 7 | 8 | 10 |
| 2024 | 2 | 7 | 7 | 8 |
| 2025 | 2 | 8 | 8 | 10 |
| 2026 | 2 | 8 | 8 | 11 |

## (b) Le 23 operazioni vere (`research/opzioni_import/storico_prezzi_veri.csv`)
Superficie valutata al giorno d'ingresso, all'ora 00:00 UTC, con F = prezzo implicito in `K_su_S` (K/S − 1). Il premio
vero è il prezzo medio degli scambi veri del contratto in BTC (premio/prezzo).

Operazioni valutate: 23/23. Volatilità (superficie − vera, punti di vol): mediana +0.6, mediana assoluta 0.8, massimo assoluto 10.6.
Premio (superficie/vero − 1), con il prezzo del momento d'ingresso (S = K/(1+K_su_S)): mediana -3.1%, mediana assoluta 4.7%, massimo assoluto 14.5%.
Premio con lo spot mediano del giorno (spot(D)) invece del prezzo d'ingresso: mediana -3.9%, mediana assoluta 7.9%, massimo assoluto 61.9%.

Attenzione: il confronto non è indipendente, perché gli scambi veri del contratto nel giorno d'ingresso possono far parte
del campione della superficie; misura soprattutto la coerenza del metodo (fasce, mediane, Black-76 con F = indice).
Lo scarto sul premio con la stessa IV viene da F = indice invece del future (base) e dall'ora degli scambi veri;
con lo spot mediano del giorno gli scarti esplodono nei giorni di forte movimento: per prezzare un ingresso
passare sempre F = prezzo del momento.

| n | entra | contratto | iv vera | iv sup. | qualità | premio vero (BTC) | premio sup. (BTC) | scarto premio | premio sup. con spot del giorno |
|---|---|---|---|---|---|---|---|---|---|
| 1 | 2018-01-08 | BTC-26JAN18-16000-C | 1.423 | 1.446 | scambi | 0.1468 | 0.1351 | -7.9% | -31.0% |
| 2 | 2018-04-30 | BTC-25MAY18-9000-C | 0.853 | 0.926 | scambi | 0.1176 | 0.1192 | +1.4% | -3.9% |
| 3 | 2018-10-15 | BTC-28DEC18-6250-P | 0.641 | 0.600 | scambi | 0.1088 | 0.1006 | -7.5% | -7.9% |
| 4 | 2019-05-13 | BTC-28JUN19-7000-C | 0.783 | 0.843 | scambi | 0.1082 | 0.1179 | +9.0% | +61.9% |
| 5 | 2020-02-10 | BTC-27MAR20-10000-C | 0.615 | 0.611 | scambi | 0.1101 | 0.0942 | -14.5% | -26.5% |
| 6 | 2020-03-16 | BTC-24APR20-5500-P | 1.488 | 1.594 | scambi | 0.2105 | 0.2230 | +5.9% | +35.4% |
| 7 | 2020-05-04 | BTC-29MAY20-9000-C | 0.723 | 0.762 | scambi | 0.0716 | 0.0751 | +4.8% | -7.3% |
| 8 | 2020-10-26 | BTC-27NOV20-13000-C | 0.517 | 0.502 | scambi | 0.0682 | 0.0611 | -10.5% | -8.5% |
| 9 | 2020-12-14 | BTC-29JAN21-19000-C | 0.647 | 0.656 | scambi | 0.1073 | 0.0976 | -9.0% | -9.6% |
| 10 | 2021-02-01 | BTC-26FEB21-34000-C | 1.113 | 1.116 | scambi | 0.1100 | 0.1057 | -3.8% | +2.9% |
| 11 | 2021-08-02 | BTC-27AUG21-40000-C | 0.804 | 0.798 | scambi | 0.0860 | 0.0825 | -4.0% | -7.3% |
| 12 | 2021-10-04 | BTC-29OCT21-50000-C | 0.771 | 0.790 | scambi | 0.0694 | 0.0674 | -2.8% | -9.5% |
| 13 | 2022-01-03 | BTC-28JAN22-48000-P | 0.663 | 0.670 | scambi | 0.0764 | 0.0793 | +3.8% | +8.3% |
| 14 | 2022-08-15 | BTC-30SEP22-24000-P | 0.661 | 0.669 | scambi | 0.0865 | 0.0886 | +2.5% | +7.7% |
| 15 | 2023-01-23 | BTC-24FEB23-23000-C | 0.580 | 0.585 | scambi | 0.0657 | 0.0639 | -2.7% | -2.2% |
| 16 | 2023-10-23 | BTC-24NOV23-30000-C | 0.475 | 0.480 | scambi | 0.0602 | 0.0573 | -4.9% | +6.9% |
| 17 | 2024-02-12 | BTC-29MAR24-48000-C | 0.495 | 0.533 | scambi | 0.0820 | 0.0791 | -3.6% | -1.5% |
| 18 | 2024-09-23 | BTC-25OCT24-64000-C | 0.497 | 0.499 | scambi | 0.0594 | 0.0566 | -4.7% | -6.9% |
| 19 | 2025-04-28 | BTC-30MAY25-94000-C | 0.451 | 0.456 | scambi | 0.0550 | 0.0533 | -3.1% | -3.8% |
| 20 | 2025-12-01 | BTC-26DEC25-90000-P | 0.477 | 0.487 | scambi | 0.0474 | 0.0496 | +4.7% | +51.0% |
| 21 | 2026-05-25 | BTC-26JUN26-76000-P | 0.346 | 0.345 | scambi | 0.0339 | 0.0346 | +2.0% | -4.3% |
| 22 | 2026-08-24 | BTC-25SEP26-78000-C | 0.406 | 0.411 | scambi | 0.0496 | 0.0476 | -4.0% | -9.8% |
| 23 | 2026-11-16 | BTC-25DEC26-65000-P | 0.399 | 0.404 | scambi | 0.0475 | 0.0506 | +6.6% | +14.7% |

## (c) Volatilità a 30 giorni alla pari contro DVOL (dal 2021-03)
Superficie: media call/put a ln(K/F) = 0, T = 30 giorni (interpolazione della varianza totale fra le scadenze). DVOL:
media fra apertura e chiusura del giorno.

Giorni confrontati: 2071 (dal 2021-03-24 al 2026-11-23). Correlazione dei livelli: 0.989; correlazione delle variazioni giornaliere: 0.741. Scarto mediano (superficie − DVOL): -3.0 punti di vol; mediana assoluta 3.0; 95° percentile assoluto 10.9. Esclusi i giorni 'estesa': 2071 giorni, correlazione 0.989.

DVOL misura la varianza a 30 giorni su tutta la curva (ali comprese, stile VIX): è atteso che stia sopra la volatilità
alla pari, di più quando lo skew è ripido (2021–2022). Nessun giorno dei dati ha qualità "estesa": ogni giorno dal
2018-01-01 ha scambi nel campione.

| anno | giorni | correlazione | scarto mediano (punti) |
|---|---|---|---|
| 2021 | 283 | 0.951 | -8.6 |
| 2022 | 365 | 0.954 | -7.4 |
| 2023 | 365 | 0.989 | -3.7 |
| 2024 | 366 | 0.992 | -2.0 |
| 2025 | 365 | 0.993 | -1.7 |
| 2026 | 327 | 0.989 | -1.8 |

## (d) Limiti noti
- Campione, non volume completo: dal 2020 circa le 3 pagine coprono solo alcune ore (00–04, 08–12, 16–20 UTC circa);
  la mediana del giorno pesa queste ore. Le scadenze lontane e le ali (±20/40%) restano spesso senza scambi nel
  campione e vengono interpolate/estese.
- F ≈ indice spot, non il future della scadenza: con base positiva (contango, tipico 2020–2021) le call in denaro e le put
  fuori denaro risultano con moneyness leggermente spostata; l'effetto sulle IV per fascia è piccolo ma non nullo.
- L'IV è quella dello scambio fornita da Deribit (calcolata sul mark del future); le mediane per fascia con 1–2 scambi
  sono rumorose (colonna `n`). Nessun filtro su scambi in blocco o anomali oltre 1% < IV < 500%.
- spot(D) è la mediana dell'indice nel campione del giorno: nei giorni di forte movimento differisce dall'apertura
  (es. 2018-01-08, 2019-05-13). Per prezzare un ingresso passare F = prezzo del momento (parametro `F` di iv/prezzo).
- "estesa" usa il giorno precedente (fino a 3 giorni) con la stessa moneyness: nessun anticipo del futuro, ma il
  sorriso non segue i movimenti di quei giorni.
- Il file contiene anche le scadenze del giorno stesso (gg < 0, scambi prima delle 08:00) e le giornaliere: IV estreme
  (546 righe fuori da 10%–300%, quasi tutte a meno di 1 giorno o nelle ali ±40%) sono scambi veri, non filtrati;
  superficie.py non usa scadenze a meno di 2 giorni per interpolare. Il 14% delle righe ha un solo scambio (`n` = 1).
- Black-76 senza tassi né base; Deribit quota in BTC (opzioni inverse): premio_BTC = premio_USD / F.
