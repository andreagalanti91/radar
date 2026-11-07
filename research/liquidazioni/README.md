# Liquidazioni vicine e S/R · studio del 07/11/2026 (lezione 81)

**Domanda dell'utente**: le liquidazioni vicine (stile whalebot / heatmap) aiutano a capire dove va BTC, da sole o insieme a
supporti e resistenze? Possono migliorare W2 + MACD?

**Verdetto**: no per W2. La mappa stimata non attira il prezzo (T1 0/6) e la confluenza con S/R non cambia rimbalzi e rotture
(T3 0/2). Lo squilibrio sopra/sotto ha un effetto sulle 12–24 ore (T2 1 giorno +6,5 punti, 12 ore +11,7), ma è in gran parte
momentum di breve (correlazione 0,63 con le 24 ore precedenti) e sparisce a 3–7 giorni: inutile per un sistema settimanale.
Resta contesto visivo (pagina Liquidazioni, card in Oggi).

## Metodo (preregistrato in PREREG.md, prima dei risultati)
- Dati: Binance USDT-M, OI 5 minuti (archivio metrics) + candele 1h, 2021-01 → 2026-11-02; OI alla chiusura dell'ora = ultimo valore
  DENTRO l'ora (corretto l'errore di allineamento di 55 minuti della lezione 72).
- Mappa giornaliera con `radar/liqmap.build` (identica alla dashboard): 21 giorni, leve 10/25/50/100x (30/30/25/15%), MM 0,5%.
- Split P1 2021–23 / P2 2024–26; criterio: effetto ≥ 5 punti, p < 0,05, stesso segno nelle due metà; famiglia ≥ 2/3.

## Risultati (risultati.txt, risultati_t2.txt)
| Test | Esito | Numeri |
|---|---|---|
| T1 calamita, sopra 1/3/7g | no | toccato 30,8/51,6/66,7% contro 30,8/51,3/65,5% a pari distanza; P1 +4/+5, P2 −4/−3 |
| T1 calamita, sotto 1/3/7g | no | 32,6/54,3/68,9% contro 32,8/52,9/66,8% (7g p 0,04 ma +2,1 punti, segni opposti fra le metà) |
| T2 direzione 1g | sì (da solo) | lato pesante per primo 71,4% contro 64,9% atteso, n 801, p < 0,001, P1 +6,3 · P2 +6,7 |
| T2 direzione 3g / 7g | no | +1,8 (p 0,20) / +0,5 (p 0,71) |
| T3 confluenza con S/R | no | rimbalzo 42,2% (1.361 tocchi confluenti) contro 43,3% (1.497 non confluenti), perm. p 0,57 |

Controlli NON preregistrati su T2 (dichiarati come tali): soglie 10/30/40% → +5,0/+7,8/+7,6; lato a caso −0,5; momentum 24h da
solo +4,1; squilibrio contro momentum +6,9 (n 138, p 0,11: non conclusivo).

## Limiti
- È una STIMA: lati e leve reali non sono pubblici; Binance è ~60–70% dell'OI dei perp, OKX si aggiunge solo dal vivo.
- I giorni si sovrappongono (orizzonti 3–7 giorni): i p-value sono ottimisti.
- Le liquidazioni reali OKX si raccolgono solo dal 30/10/2026 (data/liquidations.csv): fra qualche mese si potrà verificare la
  mappa contro gli eventi reali.

## File
- `PREREG.md` preregistrazione · `magnet.py` T1–T3 (`python research/liquidazioni/magnet.py [cartella archivio]`) ·
  `t2_check.py` controlli su T2 · `risultati*.txt` output.
- Codice in produzione: `radar/liqmap.py` (mappa, cluster, balene Hyperliquid), `radar/orderbook.py` (motore del book),
  `radar/pages/liquidazioni.html` (pagina).
