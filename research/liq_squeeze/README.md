# Squeeze da squilibrio delle liquidazioni con fascia DCA · 13/11/2026 · RESPINTA

**Verdetto: RESPINTA (nessuna regola passa; nemmeno "per carta").** Long quando i long sono stati puliti e sopra c'è carburante di
short (L1/L2/L3) e lo short simmetrico (S1) perdono dal 2021 dopo costi e funding, nei due periodi, in tutti i vicini, e non si
distinguono dal caso (placebo p 0,38–0,83). Il momentum a 24h con lo stesso schema di trade fa meglio. Metà degli ingressi W3 sulla
fascia DCA: 74,2k contro 78,5k (meglio nel 2021–23, peggio dal 2024): respinta come la lezione 92.

Regole e soglie in PREREG.md (scritto prima dei risultati). Mappa `radar/liqmap.build` ricostruita OGNI ORA dal 22/01/2021 con le
504 ore precedenti (50.913 mappe, nessun look-ahead), cascate come `radar/liqcascade` (≥ 3% in ≤ 8h, ≥ 2 fasce dense della mappa di
partenza), ingresso alla barra successiva, 0,08% per lato + funding reale, 10k a 1x, una posizione alla volta, DD giornaliero.

## Risultati (10k, 1x, dal 22/01/2021; media e PF per trade)
| Regola | Finale | DD | Trade | WR | PF | Media IS | Media OOS | Placebo ore / mappe | Senza top 3 |
|---|---|---|---|---|---|---|---|---|---|
| L1 squilibrio + pulizia, a mercato | 4.773 | −68,6% | 311 | 61% | 0,88 | −0,29% | +0,04% | p 0,42 / 0,38 | 3.833 |
| L2 come L1 con DCA (3 limit, 24h) | 4.554 | −66,7% | 214 | 51% | 0,77 | −0,45% | −0,04% | p 0,76 / 0,80 | 3.737 |
| L3 = L2 senza pulizia | 4.697 | −67,9% | 227 | 52% | 0,79 | −0,44% | +0,04% | p 0,71 / 0,71 | 3.854 |
| S1 short simmetrico (DCA) | 4.604 | −66,2% | 365 | 53% | 0,86 | −0,29% | −0,02% | p 0,83 / 0,80 | 3.698 |
| Momentum 24h + (stessa frequenza), schema L2 | 7.289 | −44,0% | 168 | 58% | 0,88 | −0,27% | +0,10% | | |
| Momentum 24h − ("compra la discesa"), schema L2 | 15.909 | −55,1% | 181 | 45% | 1,21 | +0,12% | +0,88% | | |
| Pulizia sola (L2 senza S) | 8.598 | −63,6% | 585 | 45% | 1,02 | +0,08% | −0,03% | | |
| W3 (riferimento) | 78.474 | −21,1% | 13 | 92% | | | | | |
| W3-DCA (metà a mercato, metà su 3 limit) | 74.152 | −23,0% | 13 | | | 33,8k vs 33,5k | 23,0k vs 23,5k | | |
| Buy & hold | 23.159 | −76,7% | 1 | | | | | | |

Periodi (solo trade del periodo): L1 2021–23 4.800 (PF 0,83), 2024→ 9.943 (PF 1,03); L2 4.752 / 9.585; L3 4.658 / 10.084;
S1 4.942 / 9.316. Il trade medio di ore casuali con lo stesso schema vale −0,20% (costi + funding): le regole sono lì.

## Robustezza
- Vicini con PF > 1: L1 0/12, L2 0/12, L3 1/6, S1 0/12 (soglia 0,3/0,7, raggio ±4/±8%, uscita 3/7 giorni, pulizia 48/96h,
  percentile 10/30, solo cascata / solo percentile). Il migliore (raggio ±8%) è a pareggio (PF 0,99–1,02), negativo nel 2021–23.
- Cosa aggiunge la pulizia: nulla (L2 −0,32%/trade contro L3 −0,29%). Cosa aggiunge S alla pulizia: peggiora (pulizia sola +0,03%).
- Sizing a rischio fisso: 0,5% → 9,6k (L1), 9,1k (L2), 9,1k (S1); 1% → 9,2k / 8,2k / 8,2k; solo con W3 flat: 9,6k / 9,6k / 10,2k
  (S1, PF 1,07, rumore). Nessuna versione aggiunge valore a W3.
- Criteri (≥ 30 trade, PF ≥ 1,2, IS e OOS > 0, OOS > momentum, placebo p < 0,0083, vicini ≥ 2/3, senza top 3 > 10k): ogni regola
  soddisfa solo il numero di trade.
- Limite noto: in L2 il limit resta valido anche se il prezzo tocca prima il target 1 (selezione avversa come in lezione 92); non
  cambia il verdetto perché L1 a mercato perde lo stesso.

## Stato di oggi (decisione 13/11 08:00 UTC, ultima ora chiusa 07–08, prezzo 68.594; OI Binance vero fino alle 23:00, poi stimato da OKX)
- Mappa stimata (solo Binance USDT-M): entro ±6% short sopra **$6M**, long sotto **$106M** → S = **−89%**. Entro ±10%: 88M short,
  108M long; fino a 76k 129M di short. La lettura Coinglass dell'utente (~$1,2B di short sopra) non si ritrova nella stima Binance:
  gli short vicini sono stati spazzati dal massimo di 71,5k e i grandi cluster short sono a 74,0–74,8k (+8/9%).
- Pulizia long: sì (cascata long con ultima ora valida 07:00 UTC; long sotto al 2° percentile di 90 giorni).
- **L1/L2: nessun setup** (serve S ≥ +50%). Piano ipotetico long, solo informativo: limit 68.002 / 67.409 / 66.817 (fascia densa
  66,8k, $52M, dentro il supporto 66.956–70.080), stop 65.716 (−2,5% dal prezzo medio), T1 74.020, T2 74.391, uscita a 5 giorni.
- Le regole segnalano invece **S1 short** (S −89%, short sopra al percentile 0,1%): limit 69.280 / 69.966 / 70.652, stop 71.753,
  T1 66.817, T2 66.153. Regola respinta: non operare.

## File
PREREG.md · sq_data.py (mappe orarie) · sq_bt.py (motore) · sq_run.py (studio) · sq_oggi.py (stato di oggi → oggi.json) ·
squeeze.py (modulo candidato: `state(report, ...)`) · risultati.txt · regole.csv · vicini.csv · sizing.csv · w3_dca.csv ·
w3_dca_trade.csv · trade_L1.csv, trade_L2.csv, trade_L3.csv, trade_S1.csv. Cache in /tmp/radar-work/liqsqueeze/.

## Lezione proposta (93)
**Lezione 93**: entrare quando un lato delle liquidazioni stimate è stato pulito e l'altro è carico (squeeze) non dà vantaggio su
BTC dal 2021: con mappe orarie senza look-ahead, 214–365 trade per regola, long e short, a mercato o con DCA su 3 limit, tutte
perdono dopo costi (PF 0,77–0,88, ~10k → 4,6–4,8k), nei due periodi e in 41 vicini su 42, e non si distinguono da ore o mappe
casuali (p 0,38–0,83). La pulizia non aggiunge nulla e lo squilibrio peggiora la sola pulizia; il momentum a 24h con lo stesso
schema fa meglio (lezione 81). Metà degli ingressi W3 sulla fascia DCA costa 4k (lezione 92). Lo stato squeeze resta al più
contesto in dashboard; la mappa Binance stimata e quella Coinglass possono dare letture opposte sullo stesso giorno.
