# Dimensione ridotta di W3.2 (trend affollati, long giovani, short tardi) · 27/11/2026 · NESSUNA VARIANTE PASSA

**Verdetto** (PREREG f558fb4, conteggi 010ee98, nessuna deviazione dalle regole: DEVIAZIONI.md)
- **D1 affollato** (OI 28 g o funding 7 g sopra il p90 dell'anno): **non passa**. ETH migliora molto, ma BTC peggiora (68,8k contro 84,8k $), il capitale insieme scende del 6,9% e i vicini non reggono.
- **D2 giovane** (prime 3 settimane sopra la SMA40): **non passa**. Riduce 12 operazioni su 19, quindi è quasi un rischio più basso per tutti i long: capitale insieme −22%, OOS peggiore su entrambi gli asset.
- **D3 = D1 ∪ D2:** **non passa**. Capitale insieme −22%, BTC peggiore in tutti i periodi.
- **D4 short tardo** (oltre il 35% sotto la SMA40): **non passa**. È l'unica che migliora ovunque tocchi, ma cambia 1 operazione su BTC e 2 su ETH, il vicino al 30% è sotto W3.2 e il placebo dà p 0,10 (non può passare Holm per costruzione).

**Scelta finale (PREREG §6): nessuna. W3.2 resta com'è.**

## Risultati
10.000 $ per asset a 1x, costi e funding inclusi, partenza da flat, fine 24/11/2026, DD giornaliero. Celle: capitale finale $ /
DD % / CAGR/DD. Insieme = BTC + ETH, 10.000 $ ciascuno dal 11/01/2021. Le operazioni non cambiano mai (23 BTC dal 2018, 14 BTC
dal 2021, 15 ETH; WR 77,3 / 92,3 / 57,1%): cambia solo la dimensione di quelle toccate.

| Variante | BTC dal 2018 | BTC dal 2021 | ETH dal 2021 | Insieme | OOS 2023→ BTC · ETH | Toccate (BTC18/BTC21/ETH) |
|---|---|---|---|---|---|---|
| **W3.2** | **242.755 / −37,3 / 1,16** | **84.820 / −21,1 / 2,07** | **39.572 / −27,5 / 0,96** | **124.392 / −20,2 / 1,81** | **1,33 · 0,64** | – |
| D1 | 196.818 / −37,3 / 1,07 | 68.769 / −19,3 / 2,00 | 46.996 / −21,6 / 1,40 | 115.765 / −17,8 / 1,96 | 1,27 · 1,07 | 3 / 3 / 4 |
| D2 | 167.202 / −35,6 / 1,05 | 60.906 / −16,9 / 2,13 | 36.348 / −25,3 / 0,97 | 97.254 / −16,9 / 1,83 | 1,26 · 0,57 | 9 / 6 / 6 |
| D3 | 151.688 / −35,6 / 1,00 | 55.255 / −16,9 / 2,00 | 41.301 / −17,2 / 1,59 | 96.556 / −16,9 / 1,81 | 1,12 · 1,00 | 10 / 7 / 7 |
| D4 | 269.224 / −30,4 / 1,47 | = W3.2 (0 toccate) | 41.086 / −27,5 / 0,99 | 125.906 / −20,2 / 1,82 | = · = | 1 / 0 / 2 |
| *Buy & hold* | *43.514 / −81,2 / 0,22* | *20.635 / −76,6 / 0,17* | *13.362 / −79,3 / 0,06* | – | – | – |

| Variante | Placebo p | Batte W3.2 (placebo) | Mediana placebo | Holm | Vicini (insieme CAGR/DD, W3.2 1,81) | Ripristino peggiore | Criteri falliti |
|---|---|---|---|---|---|---|---|
| D1 | 0,012 | 11,4% | 1,64 | sì | p80 1,86 (99,9k $) · p95 1,99 (118,7k $, BTC18 1,09) | BTC 04/2025 → 1,78 | 1 BTC18, 1 BTC21, 2 BTC OOS, 3, 4, 7 |
| D2 | 0,021 | 2,6% | 1,51 | sì | 2 sett. 1,82 (100,5k $) · 4 sett. 1,83 (97,3k $) | ETH 08/2026 → 1,70 | 1 BTC18, 2 BTC IS, 2 BTC/ETH OOS, 3, 4, 7 |
| D3 | 0,002 | 0,3% | 1,47 | sì | 1,62 · 1,82 (83–97k $) | ETH 08/2026 → 1,67 | 1 BTC18, 1 BTC21, 2 BTC IS e OOS, 3, 4, 7 |
| D4 | 0,102 | 21,0% | 1,80 | no | 30%: 1,80 · 40%: 1,82 | ETH 09/2022 → 1,81 | 4 (e Holm) |

Criteri: 1 = CAGR/DD più alto e DD non peggiore (BTC 2018, BTC 2021, ETH, insieme); 2 = IS/OOS non peggiori; 3 = capitale
insieme non sotto il −5% (soglia 118.172 $); 4 = vicini; 7 = non concentrato. 2021–23 / 2024→, senza la migliore e senza le due
migliori, MAR: `fase2_output.txt`.

**Come leggere i risultati**
- **Il placebo basso non è un via libera.** D1–D3 battono le riduzioni casuali (p 0,002–0,021), ma la mediana del placebo
  (1,47–1,64) sta molto sotto W3.2: dimezzare a caso 6–7 long su 9 costa molto. Il placebo dice che la scelta è meno cattiva
  del caso, non che sia migliore di W3.2 (stessa lettura di MINER-A, lezione 132).
- **D1 lavora su ETH, non su BTC.** Dimezza il long ETH del 06/2024 (−21,4%) e porta ETH da 39,6k a 47,0k $ con DD −21,6%. Su
  BTC le 3 operazioni toccate sono tutte vincenti (2023, 2024, 2025): BTC dal 2021 perde 16k $. Il caso guida BTC 2018 non è
  coperto (niente OI né funding prima del 2020). Il vicino p95 è a 1,09 su BTC 2018 (sotto 1,16): la soglia non è stabile.
- **D2 e D3 sono un "rischio più basso" mascherato.** Abbassano il DD (BTC dal 2021 −16,9%) e il capitale insieme di più del 20%:
  è l'effetto scala della lezione 101, già noto (W3.1 al 10%). Metà dei long vincenti è giovane come i perdenti.
- **D4 è un singolo episodio per asset.** Su BTC cambia solo lo short del 03/2020 (−17,9%): da qui +26k $ dal 2018 e DD da
  −37,3% a −30,4%. Su ETH cambia i 2 short persi del 2022. Il segno è coerente, ma 3 operazioni non bastano: il vicino al 30% tocca
  anche uno short vincente BTC del 2022 e scende sotto W3.2.

## Cosa significa per l'utente
- **Strategia:** W3.2 non cambia. Né su BTC né su ETH la dimensione ridotta nei casi "affollato" o "giovane" migliora il rapporto
  rendimento/rischio senza togliere troppo capitale.
- **Su ETH:** l'affollamento (OI in forte crescita) ha ridotto la perdita grande del 2024. È un'indicazione da seguire su carta,
  non una regola: 4 operazioni, e su BTC la stessa regola dimezza solo vincenti.
- **Short dopo un crollo:** aprire short oltre il 35% sotto la SMA40 è andato male 3 volte su 3. È un'osservazione da tenere,
  non una regola: si può verificare dal vivo solo nel prossimo bear.
- **Se si vuole meno DD,** la leva semplice resta il rischio per operazione uguale per tutte (lezioni 99–101), non una selezione.

## Limiti
- **Pochi trade:** le varianti toccano da 0 a 7 operazioni per asset. D4 non poteva passare Holm (10 combinazioni nel placebo).
- **Buchi nei dati:** OI Binance dal 12/2021 (soglia dal 06/2022), funding dal 2020 (soglia dal 07/2020). D1 di fatto è una
  regola sull'OI: tutte le operazioni toccate scattano per l'OI.
- **Soglie viste prima:** D2 e D4 nascono dall'analisi delle perdite. La correzione "funding sopra il tasso neutro" è stata fatta
  dopo i conteggi e prima dei rendimenti (PREREG §3). L'OOS 2023→ non è del tutto pulito, perché le perdite 2024–26 erano note.
- **Insieme sensibile al percorso:** rimettere a dimensione piena una sola operazione BTC vincente (04/2025) porta D1 sotto
  W3.2. Il CAGR/DD dell'insieme dipende da dove cade il DD massimo, non solo dalle operazioni ridotte.

## Lezione 133 proposta
**Lezione 133**: ridurre la dimensione di W3.2 invece di bloccare gli ingressi (research/dimensione, PREREG f558fb4, 4 varianti,
R 0,125 invece di 0,25, Holm m = 4): nessuna passa e W3.2 resta com'è.
- "Affollato" (OI a 28 g o funding 7 g oltre il p90 dell'anno) migliora ETH (47,0k contro 39,6k $, DD −21,6 contro −27,5,
  grazie al long del 06/2024) ma su BTC dimezza solo vincenti (68,8k contro 84,8k). Capitale insieme −6,9%, vicini instabili.
- "Long giovane" (≤ 3 settimane sopra la SMA40) e l'unione delle due regole toccano 12–14 operazioni su 19: sono un rischio più
  basso per tutti, con capitale −22% (effetto scala, lezione 101).
- "Short oltre il 35% sotto la SMA40" migliora ovunque tocchi (BTC dal 2018 269k contro 243k, DD −30,4 contro −37,3), ma cambia
  3 operazioni: vicino al 30% sotto W3.2, placebo p 0,10. È un'osservazione, non una regola.
- Un placebo basso (p 0,002–0,02) con mediana del placebo sotto W3.2 dice solo che la selezione batte il caso, non W3.2: il
  confronto decisivo resta con W3.2 e con il capitale.
- I casi guida non sono coperti dai dati: BTC 01/2018 non ha OI né funding. Le perdite grandi dei long restano un rischio
  accettato da W3.2 (tetto al 25%).

## File
`PREREG.md`, `DEVIAZIONI.md`, `regole.py` (segnali e motore, verifica 242.755 / 84.820 / 39.572 $), `conteggi.py` →
`conteggi_output.txt`, `conteggi.csv`, `fase2.py` → `fase2_output.txt`, `risultati.csv`.
