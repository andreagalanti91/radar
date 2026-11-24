# Opzioni su BTC con i segnali di W3.2: guida da zero, strategia, backtest

Per chi non ha mai usato un'opzione. Cosa sono, come usarle con i segnali del radar, cosa dicono i dati, da dove si opera.
Dati fino al 23/11/2026; quotazioni OKX del 24/11/2026.

> Ricerca su dati storici, non una raccomandazione d'investimento.

## 1. Sintesi

**La strategia è semplice: a ogni segnale di W3.2 si compra una sola opzione a circa 30 giorni (call se long, put se short)
spendendo il 5% del capitale. Rifatta con i prezzi veri delle opzioni dal 2018, rende un po' meno di W3.2 a metà dimensione. Quello che cambia è che la perdita per operazione è fissata al 5% in partenza, senza stop e senza leva. Si opera da
OKX, che usi già.**

| Domanda | Risposta |
|---|---|
| Cos'è | Un contratto che dà il diritto di comprare (call) o vendere (put) BTC a un prezzo fissato, entro una data. Si paga un premio. Se va male si perde il premio e basta |
| La strategia | Segnale di W3.2 → una call o una put a circa 30 giorni, al prezzo corrente, con il 5% del capitale. Si vende quando W3.2 esce, o si incassa a scadenza |
| Si può backtestare? | Sì, e con prezzi veri: l'archivio pubblico di Deribit ha gli scambi di tutte le opzioni scadute. Ho rifatto le 23 operazioni di W3.2 dal 2018 con i contratti realmente scambiati quel giorno |
| Risultato con prezzi veri | Dal 2018: 10.000 $ → 51.000 $, contro 53.000 $ di W3.2 a metà dimensione e 209.000 $ di W3.2 intera. Dal 2019: 49.000 $ contro 57.000 $ |
| Cosa cambia rispetto a W3.2 a metà | Perdita peggiore per operazione −5% invece di −12,5%; serie peggiore di perdite −8% invece di −14%. Ma operazioni in guadagno 65% invece di 78% |
| E con il 10%? | 197.000 $ contro 209.000 $ di W3.2 intera, perdita peggiore −10% invece di −25%, serie peggiore −16% invece di −27% |
| Quanto è solido | 23 operazioni, e le tre migliori fanno metà del risultato. La singola operazione dipende molto dalla scadenza disponibile quel giorno. Se i segnali di W3.2 peggiorano (metà delle operazioni in guadagno) il risultato a tre anni scende a +32% e una volta su sei si perde |
| Il modello era giusto? | Sulla volatilità sì (vera 1,02 volte il modello in mediana). Era un po' ottimista sul resto: nella realtà esistono solo le scadenze del venerdì, fra 25 e 46 giorni, e le call costano qualche punto in più perché sono prezzate sul future. Risultato dal 2019: 55.000 $ a modello, 49.000 $ con prezzi veri |
| Da dove si opera | OKX Europe offre opzioni su BTC ai clienti al dettaglio: contratto minimo 0,01 BTC (circa 35 $ di premio), premio e incasso in dollari. Bitget non ha opzioni |
| Come partire | Prima sulla carta: annotare il prezzo vero a ogni segnale. Poi con un contratto. Il 5% solo dopo aver visto almeno 3–4 operazioni |

Una verifica indipendente ha riprodotto i calcoli del backtest a modello e ne ha ridimensionato le conclusioni; il backtest
con i prezzi veri, fatto dopo e verificato a sua volta, conferma il quadro: non rende più di W3.2 a metà dimensione, ha un
profilo di perdita diverso.

## 2. Le opzioni in una pagina

**Call**: il diritto di comprare BTC a un prezzo fissato (prezzo d'esercizio) entro una data (scadenza). Guadagna se BTC sale.

**Put**: il diritto di vendere BTC a un prezzo fissato entro una data. Guadagna se BTC scende.

**Premio**: quanto costa quel diritto. Si paga subito. È tutto quello che si può perdere.

Cosa succede alla scadenza di una call con prezzo d'esercizio 60.000 $:

- BTC a 70.000 $: l'opzione vale 10.000 $ (la differenza). Su OKX non si riceve BTC: si incassa la differenza in dollari.
- BTC a 60.000 $ o meno: l'opzione vale zero. Si è perso il premio.

Per la put è lo specchio: vale la differenza se BTC è sotto il prezzo d'esercizio, zero se è sopra.

Tre cose da sapere prima di tutto:

1. **Il tempo lavora contro chi compra.** Ogni giorno che passa senza movimento l'opzione vale un po' meno. A 30 giorni dalla
   scadenza un'opzione al prezzo corrente perde circa l'1,7% del suo valore al giorno, e sempre più in fretta verso la fine.
2. **Il prezzo dipende dalla volatilità attesa.** Quando il mercato è nervoso le opzioni costano di più. La misura si chiama
   volatilità implicita: oggi è il 50% annuo, e un'opzione a 30 giorni al prezzo corrente costa il 5,6–5,9% del prezzo di BTC.
3. **Comprare e vendere non sono simmetrici.** Chi compra rischia solo il premio. Chi vende incassa il premio e rischia
   perdite senza limite: lo studio precedente (`RICERCA_NUOVA.md`) mostra che su BTC vendere è finito male. Qui si compra soltanto.

Le parole che si incontrano sulla piattaforma:

| Termine | Significato |
|---|---|
| Strike | Prezzo d'esercizio |
| Expiry | Scadenza |
| ATM (at the money) | Opzione con prezzo d'esercizio uguale al prezzo corrente: "alla pari" |
| OTM / ITM | Fuori dal prezzo (più economica, serve più movimento) / dentro il prezzo (più cara, vale già qualcosa) |
| Bid / Ask | Denaro (prezzo a cui si vende) / lettera (prezzo a cui si compra) |
| IV | Volatilità implicita |
| Delta | Di quanto cambia il prezzo dell'opzione se BTC si muove di 1 $. Alla pari è circa 0,5 |
| Theta | Quanto valore perde l'opzione in un giorno |
| Mark price | Prezzo teorico calcolato dalla piattaforma: serve da riferimento per mettere l'ordine |

### Un esempio con i prezzi veri di oggi

Quotazioni OKX del 24/11/2026, 17:39 UTC, opzioni lineari (premio e regolamento in dollari), scadenza 25/12/2026 (30 giorni). Prezzo a termine di BTC: 60.144 $. Un contratto vale 0,01 BTC.

| Opzione | Prezzo d'esercizio | Denaro (vendi a) | Lettera (compri a) | Differenza denaro-lettera | Costo di un contratto (0,01 BTC) | Volatilità implicita | Premio in % del prezzo di BTC |
|---|---|---|---|---|---|---|---|
| Put | 60.000 $ | 3.340 $ | 3.370 $ | 0,9% | 33,70 $ | 50% | 5,6% |
| Put | 61.000 $ | 3.820 $ | 3.855 $ | 0,9% | 38,55 $ | 49% | 6,4% |
| Put | 62.000 $ | 4.355 $ | 4.400 $ | 1,0% | 44,00 $ | 48% | 7,3% |
| Call | 60.000 $ | 3.495 $ | 3.525 $ | 0,9% | 35,25 $ | 50% | 5,9% |
| Call | 61.000 $ | 2.975 $ | 3.005 $ | 1,0% | 30,05 $ | 49% | 5,0% |
| Call | 62.000 $ | 2.515 $ | 2.545 $ | 1,2% | 25,45 $ | 48% | 4,2% |

Esempio: capitale 45.000 $, segnale short di W3.2, quota 5% = 2.250 $. Put con prezzo d'esercizio 60.000 $ a 3.370 $: si comprano 66 contratti (0,66 BTC, controvalore 39.695 $), spesa 2.236 $ commissioni incluse. Cosa succede alla scadenza:

| BTC alla scadenza | Variazione | Valore delle put | Guadagno o perdita | Sul capitale | Lo stesso controvalore short sul perp, senza stop |
|---|---|---|---|---|---|
| 42.101 $ | -30% | 11.808 $ | +9.572 $ | +21,3% | +11.909 $ |
| 48.115 $ | -20% | 7.838 $ | +5.601 $ | +12,4% | +7.939 $ |
| 54.130 $ | -10% | 3.867 $ | +1.631 $ | +3,6% | +3.970 $ |
| 56.612 $ | -5,9% (pareggio) | 2.229 $ | −7 $ | -0,0% | +2.331 $ |
| 60.144 $ | invariato | 0 $ | −2.236 $ | -5,0% | 0 $ |
| 66.159 $ | +10% | 0 $ | −2.236 $ | -5,0% | −3.970 $ |
| 72.173 $ | +20% | 0 $ | −2.236 $ | -5,0% | −7.939 $ |

Pareggio a scadenza: BTC a 56.612 $ (-5,9%). Perdita massima: 2.236 $ (-5,0% del capitale), qualunque cosa faccia BTC.

![Capitale nel tempo e guadagno a scadenza](results/opzioni_w32/opzioni_w32.png)

Il grafico in basso mostra la differenza con il perp. Se BTC scende molto, la put guadagna quasi quanto lo short (meno il
premio). Se BTC sale, lo short perde senza limite finché non scatta lo stop; la put si ferma al premio. Il prezzo di questa
protezione è la fascia centrale: se BTC si muove poco, il perp chiude in pari e la put perde.

## 3. Perché usarle con W3.2

W3.2 oggi apre una posizione spot o perp con uno stop a 2,5 ATR settimanali, dimensionata per perdere il 25% del capitale se
lo stop scatta. Con l'opzione cambia il modo di prendere lo stesso rischio:

| | W3.2 su spot o perp | W3.2 con opzione comprata |
|---|---|---|
| Perdita massima per operazione | Circa 25% allo stop; di più se il prezzo salta lo stop | Il premio pagato: 5% |
| Stop | Necessario, può essere saltato o preso da un movimento breve | Non serve |
| Liquidazione | Possibile con la leva | Impossibile |
| Se BTC resta fermo | Pari | Perdita del premio |
| Se BTC si muove piano nella direzione giusta | Guadagno | Poco o niente: il tempo consuma il premio |
| Se BTC si muove in fretta nella direzione giusta | Guadagno | Guadagno, amplificato |
| Durata | Finché W3.2 non esce | Al massimo 30 giorni |

W3.2 guadagna spesso nelle prime settimane dopo il segnale: per questo un'opzione breve ne cattura una buona parte. Quando
invece il movimento arriva dopo il primo mese, l'opzione è già scaduta.

## 4. La strategia

1. **Segnale**: quello di W3.2 del radar, senza modifiche. Si entra il lunedì.
2. **Cosa comprare**: una call se il segnale è long, una put se è short.
3. **Scadenza**: il venerdì più vicino a 30 giorni fra quelli disponibili (nella pratica fra 25 e 46 giorni).
4. **Prezzo d'esercizio**: il più vicino al prezzo di BTC in quel momento.
5. **Quanto**: il 5% del capitale in premio, commissioni incluse. Il resto del capitale resta fermo, in dollari.
6. **Uscita**: quando W3.2 esce, si vende l'opzione. Se l'opzione scade prima, l'incasso è automatico e si resta fuori fino al
   prossimo segnale.
7. **Mai**: rinnovare l'opzione scaduta, aumentare la quota dopo una perdita, vendere opzioni.
8. **Ordini**: sempre con prezzo limite, a metà fra denaro e lettera.

Le scelte sono poche e fissate prima: una opzione per segnale, perdita massima nota all'ingresso.

## 5. Il backtest a modello

Serve a provare molte varianti in fretta; § 7 lo rifà con i prezzi veri. Prezzi delle opzioni calcolati con la formula di Black e la volatilità implicita stimata delle opzioni alla pari. Il valore
è ricalcolato ogni giorno. "Una sola" = regola 6; "con rinnovo" = alla scadenza se ne compra un'altra finché W3.2 resta in
posizione.

Operazioni di W3.2 dal 2019-05-13: 20 (l'ultima è aperta). Durata mediana: 63 giorni. Costi: differenziale denaro-lettera 3% del premio per lato, commissione 0,03% del controvalore (tetto 7% del premio), esercizio 0,02%.

| Versione | 10.000 $ → | CAGR | Max DD (giornaliero) | Operazioni in guadagno | Operazione peggiore | Migliore | Serie peggiore di perdite | Premio speso per operazione | Opzioni per operazione |
|---|---|---|---|---|---|---|---|---|---|
| W3.2 originale (spot e perp, rischio 25% allo stop) | 236.413 | +49,4% | -37,3% | 85% | -17,9% | +52,2% | -20,0% | – | – |
| W3.2 a metà dimensione (riferimento a rischio simile) | 53.793 | +23,8% | -20,0% | 85% | -9,0% | +26,1% | – | – | – |
| W3.2 a un quinto della dimensione (riferimento a rischio simile) | 20.084 | +9,3% | -8,3% | 85% | -3,6% | +10,4% | – | – | – |
| Opzione a 30 giorni, 5% del capitale, una sola | 55.465 | +24,3% | -14,1% | 80% | -5,0% | +34,5% | -7,1% | 5,0% | 1,0 |
| Opzione a 30 giorni, 10% del capitale, una sola | 230.273 | +48,9% | -26,2% | 80% | -10,0% | +69,0% | -14,0% | 10,0% | 1,0 |
| Opzione a 60 giorni, 5% del capitale, una sola | 45.952 | +21,4% | -18,3% | 65% | -5,0% | +28,5% | -9,6% | 5,0% | 1,0 |
| Opzione a 60 giorni, 10% del capitale, una sola | 164.468 | +42,7% | -31,9% | 65% | -10,0% | +56,9% | -18,7% | 10,0% | 1,0 |
| Opzione a 90 giorni, 5% del capitale, una sola | 36.716 | +17,9% | -15,8% | 70% | -4,9% | +21,5% | -5,9% | 5,0% | 1,0 |
| Opzione a 90 giorni, 10% del capitale, una sola | 113.308 | +36,1% | -28,5% | 70% | -9,8% | +43,1% | -11,6% | 10,0% | 1,0 |
| Opzione a 30 giorni, 5% del capitale, con rinnovo | 48.005 | +22,0% | -28,3% | 60% | -8,9% | +34,5% | -14,8% | 15,7% | 3,0 |
| Opzione a 30 giorni, 10% del capitale, con rinnovo | 138.081 | +39,5% | -46,7% | 60% | -17,3% | +69,0% | -30,4% | 32,8% | 3,0 |
| Opzione a 60 giorni, 5% del capitale, con rinnovo | 35.703 | +17,5% | -19,3% | 70% | -5,0% | +26,6% | -5,7% | 9,3% | 1,8 |
| Opzione a 60 giorni, 10% del capitale, con rinnovo | 95.663 | +33,2% | -33,5% | 70% | -10,0% | +52,4% | -11,3% | 19,3% | 1,8 |
| Opzione a 90 giorni, 5% del capitale, con rinnovo | 28.428 | +14,2% | -15,8% | 65% | -4,9% | +19,2% | -5,9% | 6,9% | 1,4 |
| Opzione a 90 giorni, 10% del capitale, con rinnovo | 67.077 | +27,3% | -28,5% | 65% | -9,8% | +38,5% | -11,6% | 14,1% | 1,4 |

- **Il confronto giusto è con W3.2 a metà dimensione**, non con W3.2 intera: l'opzione al 5% rende lo stesso (+24% annuo) con
  drawdown −14% invece di −20%. Al 10% rende quanto W3.2 intera con drawdown −26% invece di −37%. Vedi però § 6: includendo
  il 2018 la differenza di drawdown sparisce.
- **Il rinnovo peggiora il drawdown, sempre.** Rinnovare ogni mese costa: nelle operazioni lunghe e lente (2022–2023, 2025) si
  spende il 25–35% del capitale in premi per un movimento piccolo. È il motivo della regola 7.
- **Scadenza breve o lunga: è soprattutto leva.** A parità di spesa l'opzione a 30 giorni muove più controvalore di quella a
  90. Fra 21 e 45 giorni il rendimento non cambia in modo distinguibile (§ 6).
- **5% contro 10%.** Il 5% è una scelta prudente, non un calcolo: dà un drawdown di −14/−20%. Il tuo limite di −35% si
  raggiunge verso il 9–10% (−26% dal 2019, −37% dal 2018). Il 5% corrisponde anche ai 2–3.000 $ che già destini alla leva.

Operazione per operazione, versione base:

| # | Verso | Entra | Esce | Movimento di BTC a favore | W3.2 originale | Opzioni comprate | Premio speso (sul capitale) | Risultato con opzioni |
|---|---|---|---|---|---|---|---|---|
| 1 | long | 2019-05-13 | 2019-06-27 | +51,4% | +51,1% | 1 | 5,0% | +1,0% |
| 2 | long | 2020-02-10 | 2020-02-17 | -2,6% | -2,6% | 1 | 5,0% | -1,3% |
| 3 | short | 2020-03-16 | 2020-04-27 | -43,8% | -17,9% | 1 | 5,0% | -5,0% |
| 4 | long | 2020-05-04 | 2020-08-03 | +24,2% | +16,0% | 1 | 5,0% | -0,9% |
| 5 | long | 2020-10-26 | 2020-11-23 | +41,0% | +40,8% | 1 | 5,0% | +28,5% |
| 6 | long | 2020-12-14 | 2020-12-31 | +50,7% | +50,4% | 1 | 5,0% | +34,5% |
| 7 | long | 2021-02-01 | 2021-02-22 | +73,1% | +52,2% | 1 | 5,0% | +22,5% |
| 8 | long | 2021-08-02 | 2021-09-27 | +8,1% | +4,3% | 1 | 5,0% | +4,8% |
| 9 | long | 2021-10-04 | 2021-11-08 | +31,0% | +20,9% | 1 | 5,0% | +13,2% |
| 10 | short | 2022-01-03 | 2022-03-28 | +0,8% | +1,0% | 1 | 5,0% | +6,7% |
| 11 | short | 2022-08-15 | 2023-01-16 | +13,9% | +8,3% | 1 | 5,0% | +6,2% |
| 12 | long | 2023-01-23 | 2023-08-17 | +14,2% | +13,3% | 1 | 5,0% | +1,5% |
| 13 | long | 2023-10-23 | 2024-01-01 | +40,7% | +40,5% | 1 | 5,0% | +14,4% |
| 14 | long | 2024-02-12 | 2024-03-11 | +42,5% | +42,2% | 1 | 5,0% | +31,5% |
| 15 | long | 2024-09-23 | 2025-02-26 | +34,0% | +30,8% | 1 | 5,0% | +0,1% |
| 16 | long | 2025-04-28 | 2025-10-10 | +11,6% | +11,3% | 1 | 5,0% | +9,6% |
| 17 | short | 2025-12-01 | 2026-04-27 | +12,8% | +11,9% | 1 | 5,0% | -3,2% |
| 18 | short | 2026-05-25 | 2026-08-20 | +4,8% | +5,7% | 1 | 5,0% | +17,5% |
| 19 | long | 2026-08-24 | 2026-11-09 | -3,9% | -4,1% | 1 | 5,0% | +6,3% |
| 20 | short | 2026-11-16 | aperta | +6,1% | +5,9% | 1 | 5,0% | +2,7% |

Dove l'opzione fa peggio: operazioni lunghe in cui BTC si muove dopo il primo mese (n. 1, 4, 12, 15, 17). Dove fa meglio: quando
W3.2 sbaglia (n. 3: −5% invece di −18%) e quando il movimento è subito forte (n. 5, 6, 14). In tre casi (n. 10, 18, 19) l'opzione
guadagna più di W3.2, che chiude in pari o in perdita, perché il movimento giusto c'è stato nel primo mese e poi è rientrato.

## 6. Quanto è solido

### Prezzo dell'opzione, costi, scadenza

| Ipotesi (versione base: 30 giorni, 5% del capitale, una sola opzione) | 10.000 $ → | CAGR | Max DD | Operazioni in guadagno | Operazione peggiore |
|---|---|---|---|---|---|
| Base | 55.465 | +24,3% | -14,1% | 80% | -5,0% |
| Volatilità al livello del DVOL, in acquisto e in vendita | 48.201 | +22,1% | -14,1% | 75% | -5,0% |
| Si compra al livello del DVOL, si rivende alla volatilità alla pari | 48.112 | +22,1% | -14,1% | 75% | -5,0% |
| Volatilità pagata +20% | 36.608 | +17,9% | -14,1% | 75% | -5,0% |
| Differenziale denaro-lettera doppio (6% per lato) | 49.920 | +22,6% | -13,9% | 75% | -5,0% |
| Tutto insieme: DVOL in acquisto, alla pari in vendita, differenziale 6% | 43.475 | +20,5% | -13,9% | 75% | -5,0% |
| Opzione 5% fuori dal prezzo (più economica, serve più movimento) | 79.800 | +30,2% | -16,5% | 65% | -5,0% |
| Opzione 5% dentro il prezzo (più cara, perde valore più lentamente) | 40.012 | +19,2% | -12,3% | 85% | -5,0% |
| Scadenza a 21 giorni invece di 30 | 54.711 | +24,1% | -11,9% | 65% | -5,0% |
| Scadenza a 25 giorni invece di 30 | 59.706 | +25,5% | -15,8% | 70% | -5,0% |
| Scadenza a 35 giorni invece di 30 | 51.483 | +23,1% | -10,0% | 80% | -5,0% |
| Scadenza a 45 giorni invece di 30 | 47.050 | +21,7% | -17,4% | 70% | -5,0% |

Dipendenza dalle operazioni migliori: tutte le 20 operazioni danno ×5,5; senza la migliore ×4,1; senza le tre migliori ×2,4 (+12,0% annuo); senza le cinque migliori ×1,7 (+6,9% annuo). Per W3.2 originale: ×24,7, ×16,2, ×7,1.

- **Prezzo dell'opzione.** Pagare la volatilità il 20% in più toglie un terzo del capitale finale (da 55.000 a 37.000 $):
  circa 3 punti di rendimento annuo ogni 10% di prezzo. Il risultato resta positivo, ma non è indifferente.
- **Costi.** Raddoppiare la differenza denaro-lettera costa meno di 2 punti annui.
- **Giorno di scadenza.** Fra 21 e 45 giorni il rendimento sta fra +22% e +26%: nessuna scadenza è chiaramente migliore. Ma
  il drawdown va da −10% a −17% e le operazioni in guadagno dal 65% all'80%: l'80% della versione a 30 giorni è il valore più
  alto della griglia. Su OKX le scadenze sono solo il venerdì, quindi il giorno esatto non si sceglie.
- **Poche operazioni contano molto.** Senza le tre migliori il rendimento scende a +12% annuo, senza le cinque migliori a +7%.

### Il 2018, con la volatilità stimata e la scadenza a 30 giorni esatti

Per il 2018 non esistono dati di volatilità implicita: si usa la volatilità realizzata dei 30 giorni precedenti aumentata del 10%. Operazioni: 23.

| Dal 2018 | 10.000 $ → | CAGR | Max DD (giornaliero) | Operazioni in guadagno | Operazione peggiore |
|---|---|---|---|---|---|
| W3.2 originale | 209.002 | +40,8% | -37,3% | 78% | -25,1% |
| W3.2 a metà dimensione | 50.981 | +20,1% | -20,0% | 78% | -12,5% |
| Opzioni a 30 giorni, 5% | 48.333 | +19,4% | -20,0% | 70% | -5,0% |
| Opzioni a 30 giorni, 10% | 173.688 | +37,9% | -36,7% | 70% | -10,0% |
| Opzioni a 35 giorni, 5% | 50.132 | +19,9% | -12,0% | 74% | -5,0% |
| Opzioni a 25 giorni, 5% | 51.807 | +20,3% | -21,3% | 61% | -5,0% |

Le tre operazioni del 2018: long del 2018-01-08, W3.2 -25,1%, opzione -4,7%; long del 2018-04-30, W3.2 -3,3%, opzione -3,7%; short del 2018-10-15, W3.2 +16,7%, opzione -5,0%.

Con il 2018 dentro, l'opzione al 5% e W3.2 a metà dimensione sono uguali: +19–20% annuo, drawdown −20%. In questa prova le
tre operazioni del 2018 perdono tutte con l'opzione, compresa quella che W3.2 chiude a +16,7%: lo short di ottobre scade il
giorno prima del crollo di novembre. Con i contratti veri (§ 7) quel giorno la scadenza disponibile era a 74 giorni, e la
stessa operazione chiude a +14%. È la misura di quanto pesa il caso sulla singola operazione.

### Se i segnali peggiorano

Si estraggono a caso 8 operazioni (circa tre anni) dalle 20 dello storico, 5.000 volte, ognuna con il suo percorso giornaliero: il drawdown comprende anche le oscillazioni a operazione aperta.

| Versione | Risultato mediano a 3 anni | 5° percentile | Probabilità di chiudere in perdita | Drawdown mediano | Probabilità di drawdown oltre −20% | oltre −35% |
|---|---|---|---|---|---|---|
| W3.2 originale | +263% | +61% | 0% | -21% | 58% | 4% |
| W3.2 a metà dimensione | +98% | +33% | 0% | -11% | 2% | 0% |
| Opzioni a 30 giorni, 5%, una sola (base) | +95% | +26% | 0% | -9% | 0% | 0% |
| Opzioni a 30 giorni, 10%, una sola | +245% | +52% | 0% | -16% | 11% | 0% |
| Opzioni a 30 giorni, 10%, con rinnovo | +178% | +1% | 5% | -36% | 100% | 55% |
| Opzioni a 90 giorni, 10%, una sola | +169% | +39% | 1% | -21% | 53% | 1% |
| Base, se le operazioni in guadagno scendono dall'80% al 65% | +61% | +3% | 4% | -10% | 2% | 0% |
| Base, se scendono al 50% | +32% | -14% | 16% | -13% | 11% | 0% |
| Base, se scendono al 35% | +6% | -26% | 41% | -17% | 32% | 0% |

- Nei percorsi simulati l'opzione al 5% e W3.2 a metà dimensione sono vicine: rendimento mediano a tre anni +95% e +98%,
  drawdown mediano −9% e −11%.
- **La strategia vale quanto i segnali di W3.2.** Dal 2019 l'80% delle operazioni ha chiuso in guadagno. Se quella quota
  scende al 50%, a tre anni il risultato mediano è +32% e una volta su sei si chiude in perdita. Se scende al 35% non si
  guadagna più. La perdita resta lenta: 5% per volta.
- Gli altri punti deboli sono quelli visti sopra: prezzi da modello, poche operazioni decisive, il caso sulla scadenza.

## 7. Il backtest con i prezzi veri

Deribit è il mercato dove si scambia la maggior parte delle opzioni su BTC, e pubblica tutti gli scambi dei contratti
scaduti. Per ogni operazione di W3.2:

- all'ingresso si prende, fra le opzioni davvero scambiate nelle 12 ore intorno, la scadenza più vicina a 30 giorni e il
  prezzo d'esercizio più vicino al prezzo di BTC;
- il prezzo pagato è calcolato con la volatilità implicita di quegli scambi;
- all'uscita si usa la volatilità degli scambi dello stesso contratto in quel momento; se l'opzione scade prima, il valore
  alla scadenza.

Operazioni di W3.2: 23; con un'opzione vera vicina al prezzo scambiata all'ingresso: 23. Prezzi ricalcolati alla volatilità implicita degli scambi veri di Deribit; costi: differenziale 3% del premio per lato, commissioni Deribit (0,03% del controvalore, tetto 12,5% del premio; regolamento 0,015%).

| # | Verso | Entra | Esce | Contratto vero | Giorni alla scadenza | Volatilità vera | Volatilità del modello | Come finisce | W3.2 originale | Opzione, 5% del capitale: prezzi veri | Modello a 30 giorni |
|---|---|---|---|---|---|---|---|---|---|---|---|
| 1 | long | 2018-01-08 | 2018-01-16 | BTC-26JAN18-16000-C (scadenza fuori da 20–50 giorni) | 18 | 142% | n/d | venduta | -25,1% | -5,0% | n/d |
| 2 | long | 2018-04-30 | 2018-05-14 | BTC-25MAY18-9000-C | 25 | 85% | n/d | venduta | -3,3% | -3,6% | n/d |
| 3 | short | 2018-10-15 | 2019-04-02 | BTC-28DEC18-6250-P (scadenza fuori da 20–50 giorni) | 74 | 64% | n/d | scadenza | +16,7% | +13,9% | n/d |
| 4 | long | 2019-05-13 | 2019-06-27 | BTC-28JUN19-7000-C | 46 | 78% | 92% | uscita: nessuno scambio, volatilità del modello | +51,1% | +17,1% | +1,0% |
| 5 | long | 2020-02-10 | 2020-02-17 | BTC-27MAR20-10000-C | 46 | 61% | 54% | venduta | -2,6% | -1,3% | -1,3% |
| 6 | short | 2020-03-16 | 2020-04-27 | BTC-24APR20-5500-P | 39 | 149% | 171% | scadenza | -17,9% | -5,0% | -5,0% |
| 7 | long | 2020-05-04 | 2020-08-03 | BTC-29MAY20-9000-C | 25 | 72% | 72% | scadenza | +16,0% | -1,1% | -0,9% |
| 8 | long | 2020-10-26 | 2020-11-23 | BTC-27NOV20-13000-C | 32 | 52% | 50% | venduta | +40,8% | +23,7% | +28,5% |
| 9 | long | 2020-12-14 | 2020-12-31 | BTC-29JAN21-19000-C | 46 | 65% | 53% | venduta | +50,4% | +18,7% | +34,5% |
| 10 | long | 2021-02-01 | 2021-02-22 | BTC-26FEB21-34000-C | 25 | 111% | 110% | uscita: scambi entro 4 giorni | +52,2% | +25,8% | +22,5% |
| 11 | long | 2021-08-02 | 2021-09-27 | BTC-27AUG21-40000-C | 25 | 80% | 78% | scadenza | +4,3% | +5,4% | +4,8% |
| 12 | long | 2021-10-04 | 2021-11-08 | BTC-29OCT21-50000-C | 25 | 77% | 72% | scadenza | +20,9% | +10,3% | +13,2% |
| 13 | short | 2022-01-03 | 2022-03-28 | BTC-28JAN22-48000-P | 25 | 66% | 65% | scadenza | +1,0% | +9,9% | +6,7% |
| 14 | short | 2022-08-15 | 2023-01-16 | BTC-30SEP22-24000-P | 46 | 66% | 64% | scadenza | +8,3% | +5,2% | +6,2% |
| 15 | long | 2023-01-23 | 2023-08-17 | BTC-24FEB23-23000-C | 32 | 58% | 49% | scadenza | +13,3% | -2,3% | +1,5% |
| 16 | long | 2023-10-23 | 2024-01-01 | BTC-24NOV23-30000-C | 32 | 47% | 41% | scadenza | +40,5% | +15,0% | +14,4% |
| 17 | long | 2024-02-12 | 2024-03-11 | BTC-29MAR24-48000-C | 46 | 50% | 48% | venduta | +42,2% | +21,5% | +31,5% |
| 18 | long | 2024-09-23 | 2025-02-26 | BTC-25OCT24-64000-C | 32 | 50% | 49% | scadenza | +30,8% | -0,5% | +0,1% |
| 19 | long | 2025-04-28 | 2025-10-10 | BTC-30MAY25-94000-C | 32 | 45% | 47% | scadenza | +11,3% | +5,3% | +9,6% |
| 20 | short | 2025-12-01 | 2026-04-27 | BTC-26DEC25-90000-P | 25 | 48% | 47% | scadenza | +11,9% | -3,5% | -3,2% |
| 21 | short | 2026-05-25 | 2026-08-20 | BTC-26JUN26-76000-P | 32 | 35% | 35% | scadenza | +5,7% | +23,4% | +17,5% |
| 22 | long | 2026-08-24 | 2026-11-09 | BTC-25SEP26-78000-C | 32 | 41% | 40% | scadenza | -4,1% | +2,5% | +6,3% |
| 23 | short | 2026-11-16 | aperta | BTC-25DEC26-65000-P | 39 | 40% | 41% | venduta | +5,9% | +3,1% | +2,7% |

| Periodo e versione | Operazioni | 10.000 $ → | Operazioni in guadagno | Operazione peggiore | Migliore | Serie peggiore di perdite | Senza le tre migliori |
|---|---|---|---|---|---|---|---|
| Dal 2019 · W3.2 originale | 20 | 246.794 | 85% | -17,9% | +52,2% | -20,0% | ×7,1 |
| Dal 2019 · W3.2 a metà dimensione | 20 | 56.931 | 85% | -9,0% | +26,1% | -10,1% | ×2,9 |
| Dal 2019 · opzioni 5%, prezzi veri | 20 | 48.543 | 70% | -5,0% | +25,8% | -7,2% | ×2,5 |
| Dal 2019 · opzioni 5%, modello (30 giorni esatti) | 20 | 55.465 | 80% | -5,0% | +34,5% | -7,1% | ×2,4 |
| Dal 2019 · opzioni 10%, prezzi veri | 20 | 184.678 | 70% | -10,0% | +51,6% | -14,2% | ×5,6 |
| Dal 2019 · opzioni 5%, scambi grezzi (primo dopo l'ingresso, più vicino all'uscita) | 20 | 45.446 | 70% | -5,0% | +23,3% | -7,1% | ×2,5 |
| Dal 2018 · W3.2 originale | 23 | 208.703 | 78% | -25,1% | +52,2% | -27,5% | ×6,0 |
| Dal 2018 · W3.2 a metà dimensione | 23 | 53.064 | 78% | -12,5% | +26,1% | -14,0% | ×2,7 |
| Dal 2018 · opzioni 5%, prezzi veri | 23 | 50.642 | 65% | -5,0% | +25,8% | -8,4% | ×2,6 |
| Dal 2018 · opzioni 10%, prezzi veri | 23 | 197.205 | 65% | -10,0% | +51,6% | -16,4% | ×6,0 |

Volatilità all'ingresso, dal 2019: vera 65% in media, modello 64%; rapporto mediano vera / modello 1,02 (fra 0,85 e 1,23). Premio medio pagato: 8,0% del prezzo di BTC (modello: 7,7%). Prezzo a termine sopra il prezzo corrente, in mediana: +0,5% (massimo +2,6%). Scadenza media dei contratti veri: 34 giorni (fra 25 e 46).

- **Con prezzi veri l'opzione al 5% rende un po' meno di W3.2 a metà dimensione**: 51.000 $ contro 53.000 $ dal 2018, 49.000 $
  contro 57.000 $ dal 2019. Con 23 operazioni la differenza non è significativa: togliendone una sola il totale cambia fino al
  14% in più o in meno.
- **Il profilo è diverso.** L'opzione perde più spesso (35% delle operazioni contro 22%) ma poco per volta: mai più del 5%, e
  la serie peggiore di perdite è −8% contro −14%. Nel 2018 W3.2 apre con −25% alla prima operazione; l'opzione con −5%.
- **Al 10%** il risultato è vicino a W3.2 intera (197.000 $ contro 209.000 $) con perdite più contenute: peggiore operazione
  −10% invece di −25%. Sono gli stessi segnali: vale tutto quello che dice § 6 sulla dipendenza da poche operazioni.
- **Il modello era centrato sulla volatilità** (vera 65% in media, modello 64%) **e un po' ottimista sul totale**: 55.000 $ dal
  2019 contro 49.000 $ veri. Le opzioni vere sono prezzate sul future, che sta sopra il prezzo corrente (0,5% in mediana, fino
  al 2,6% nel 2021): le call costano qualche punto in più.
- **La scadenza non si sceglie.** I contratti veri avevano fra 18 e 74 giorni di vita: fino al 2019 esistevano poche scadenze.
  Dal 2020 in poi si resta fra 25 e 46 giorni.
- **Usando direttamente il primo scambio dopo l'ingresso** invece della volatilità mediana, il risultato dal 2019 è 45.000 $:
  il momento esatto dell'ordine conta.

Limiti di questo backtest: i prezzi sono ricostruiti dalla volatilità scambiata, non sono il book del momento; la
differenza denaro-lettera è una stima prudente (3% per lato; negli scambi veri è stata sotto l'1%); nel 2018–2019 gli scambi
erano pochi, in un caso uno solo; il prezzo di regolamento è quello di Binance, non l'indice Deribit.

### Controllo sui prezzi di OKX

Prezzi di chiusura giornalieri veri su OKX dei contratti oggi ancora quotati, con prezzo d'esercizio entro il 3% dal prezzo di BTC e almeno un contratto scambiato nel giorno (dal 2025-12-26 al 2026-11-17), divisi per il prezzo del modello nello stesso giorno. Sopra 1: l'opzione vera costava più del modello.

| Giorni alla scadenza | Osservazioni | Prezzo vero / modello (mediana) | Un quarto dei casi sotto | Un quarto sopra | Prezzo vero / modello al livello del DVOL (mediana) |
|---|---|---|---|---|---|
| 7–20 | 153 | 1,05 | 0,97 | 1,16 | 0,99 |
| 20–45 (la scadenza della strategia) | 318 | 1,01 | 0,96 | 1,07 | 0,95 |
| 45–90 | 403 | 1,03 | 0,96 | 1,11 | 0,97 |
| 90–180 | 404 | 1,06 | 0,97 | 1,16 | 1,00 |
| oltre 180 | 434 | 1,09 | 0,98 | 1,22 | 1,04 |

Sulla scadenza della strategia (20–45 giorni) i prezzi veri di OKX fra ottobre e novembre 2026 costavano l'1% in più del
modello. Al livello del DVOL il modello sarebbe stato troppo caro del 5%: la volatilità giusta è quella delle opzioni alla
pari. OKX conserva lo storico solo dei contratti ancora vivi, per questo il confronto copre poche settimane. La differenza
denaro-lettera vera oggi è l'1% del premio in totale; il backtest usa il 3% per lato.

## 8. Da dove si opera

| Sede | Cliente al dettaglio in Italia | Contratto minimo | Commissioni | Note |
|---|---|---|---|---|
| **OKX Europe** (Malta, licenza MiFID) | Sì, con test di appropriatezza | 0,01 BTC | 0,03% del controvalore, tetto 7% del premio; esercizio 0,02% | Opzioni lineari: premio e incasso in USD/USDC. Documento informativo (KID) in italiano |
| Deribit | Incerto | 0,1 BTC (0,01 sulle lineari) | 0,03%, tetto 12,5% del premio | Il mercato più liquido, ma senza licenza UE: base giuridica dubbia |
| Kraken Pro | Incerto | n.d. | n.d. | Opzioni nel SEE da ottobre 2026, solo su richiesta di quotazione |
| Interactive Brokers | Sì | 100 quote dell'ETF | Da broker | Opzioni sull'ETF IBIT: mercato USA, orari di borsa, non 24 ore |
| Bitget, Bybit EU, Binance | No | – | – | Bitget non risulta avere licenza UE né opzioni per l'Italia |

La scelta pratica è OKX: è l'exchange che usi, ha la licenza europea e il contratto più piccolo. Da verificare nell'app se
la sezione opzioni è già attiva sul tuo conto: i documenti la prevedono, ma non ho trovato un annuncio di lancio per l'Italia.

Come si fa, passo per passo:

1. Nell'app o sul sito: Trade → Options. Al primo accesso viene chiesto un questionario di conoscenza.
2. Scegliere BTC e la scadenza (il venerdì più vicino a 30 giorni).
3. Nella tabella dei prezzi d'esercizio scegliere la riga più vicina al prezzo di BTC: colonna Call a sinistra, Put a destra.
4. Buy, ordine Limit, prezzo a metà fra Bid e Ask, quantità in contratti (1 contratto = 0,01 BTC).
5. Per chiudere prima della scadenza: Sell sulla stessa opzione, di nuovo con ordine limite.
6. Alla scadenza (08:00 UTC del venerdì) non serve fare nulla: se l'opzione vale qualcosa l'importo viene accreditato.

Fisco, solo un cenno e da verificare con un commercialista: le plusvalenze su cripto-attività sono tassate al 33% dal 2026;
i derivati su cripto secondo i commentatori restano al 26% come redditi diversi. Con un exchange estero la dichiarazione è a
carico tuo (quadri RT e RW).

## 9. Cosa può andare storto

- **Segnali peggiori che in passato.** È il rischio principale (§ 6).
- **Campione piccolo.** 23 operazioni in nove anni.
- **Il caso sulla scadenza.** La singola operazione può passare da perdita piena a guadagno per uno o due giorni di differenza.
- **Prezzi ricostruiti.** § 7 usa la volatilità degli scambi veri, non il prezzo esatto a cui avresti comprato tu.
- **Un'operazione tagliata.** La n. 6 è chiusa il 31/12/2020 per un cambio di dati nel backtest di W3.2, non per un segnale.
- **Liquidità delle opzioni lineari.** Su OKX le quotazioni ci sono, con una differenza denaro-lettera dell'1%, ma gli scambi
  sono pochi: per importi sopra qualche BTC il prezzo può peggiorare. Per 0,5–1 BTC non è un problema.
- **Capitale fermo.** Il 95% resta in dollari senza rendere. È una scelta: è il motivo per cui il drawdown è basso.
- **Tentazione di raddoppiare.** Dopo due o tre premi persi viene voglia di alzare la quota. La regola 7 esiste per questo.

## 10. Come partire

1. **Sulla carta, da subito.** A ogni segnale di W3.2 annotare: data, prezzo di BTC, opzione scelta, prezzo lettera. All'uscita:
   prezzo denaro. Costa zero e dopo qualche operazione dice se il modello è realistico.
2. **Registrare i prezzi.** `python backtest/fetch_okx_options.py` salva la catena completa di OKX: lanciato ogni giorno
   costruisce lo storico vero che oggi manca.
3. **Un contratto.** Alla prima operazione reale, un solo contratto (circa 35 $): serve a imparare la piattaforma.
4. **La quota piena** (5%) solo dopo 3–4 operazioni seguite dall'inizio alla fine.

## 11. Fonti

- OKX Europe, condizioni di servizio e documenti informativi (KID) —
  [termini](https://www.okx.com/en-eu/help/okx-europe-market-ltd-oem-terms-of-service),
  [KID](https://www.okx.com/en-eu/help/oem-key-information-documents-kids),
  [commissioni SEE](https://www.okx.com/en-eu/help/trading-fee-rules-faq-eea)
- Deribit, giurisdizioni escluse — [pagina](https://support.deribit.com/hc/en-us/articles/25944487427741-Restricted-Jurisdictions)
- Kraken, opzioni nel SEE — [annuncio](https://blog.kraken.com/product/kraken-derivatives/options-now-available-in-the-eea)
- Interactive Brokers, opzioni su ETF USA per clienti UE — [nota](https://www.interactivebrokers.com/support/faq/content/40360001)
- Fisco 2026 — [Agenda Digitale](https://www.agendadigitale.eu/documenti/tassazione-cripto-attivita-2026-cosa-cambia-su-plusvalenze-permute-e-isee/)
- Scambi storici delle opzioni: archivio pubblico Deribit, `history.deribit.com` (`data/opzioni/deribit/`).
- Quotazioni: API pubblica OKX (`data/opzioni/okx/`). Volatilità storica: indice DVOL e scambi Deribit (`data/opzioni/`).

Codice: `backtest/opzioni_w32.py`, `backtest/opzioni_w32_reale.py`, `backtest/fetch_okx_options.py`. Tabelle: `results/opzioni_w32/tables.md`.
Studio precedente sulle opzioni vendute e sulla leva: [`RICERCA_NUOVA.md`](RICERCA_NUOVA.md).
