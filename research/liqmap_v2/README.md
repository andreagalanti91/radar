# liqmap v2 (flusso taker al posto del 50/50) · 13/11/2026 · NON ADOTTATA

**Domanda**: il 13/11 la nostra mappa (Binance USDT-M, ±5%: 45 M$ short sopra contro 146 M$ long sotto alle 19 UTC) contraddice
Coinglass (≈1,2 B$ short sopra fino a 76k, ≈150 M$ long sotto). Ipotesi: il 50/50 sui nuovi contratti; seconda: OI dopo
l'archivio stimato da OKX. Preregistrazione in PREREG.md (varianti, misure e criterio scritti prima dei risultati).

## Risultati (risultati.txt; Binance coin-margined, 476 giorni, 277 M$ di liquidazioni reali)
| Variante | M1 long (pesato) | M1 short (pesato) | M2 ρ 1 giorno | M2 ρ 3 giorni |
|---|---|---|---|---|
| v1 50/50 | 11,0% | 13,5% | −0,020 | −0,032 |
| v2 taker (principale) | 11,3% | 13,4% | −0,020 | −0,033 |
| v2k taker ×3 | 11,5% | 13,6% | −0,023 | −0,035 |
| v2t taker + top trader | 11,1% | 13,4% | −0,009 | −0,021 |
| placebo (fasce v1 di un altro giorno, stesse distanze) | 12,5% (p95 14,1) | 15,5% (p95 25,4) | | |

H1/H2: v2 − v1 = +0,7/+0,2 punti sul lato long, +0,1/−0,1 sul short: criterio (≥ 2 punti ovunque) **non raggiunto** da nessuna
variante. Nessuna mappa mette nelle 8 fasce più dense più liquidazioni reali del placebo, e il rapporto previsto short/long non
correla con quello realizzato (ρ ≈ 0). Novembre 2026 (OKX + altri, 13 giorni, indicativo): stesso quadro.

## Perché v2 cambia poco
La quota taker oraria di Binance sta quasi sempre fra 0,45 e 0,55 (dev. std 0,035): nella discesa 5–13/11 è stata 0,488–0,503.
L'ipotesi "in discesa i nuovi contratti sono short" non regge sui dati orari: ogni contratto nuovo ha un long e uno short e il
flusso taker è quasi in pari. Oggi v2 sposta la mappa di meno del 3% (oggi.txt).

## Da dove viene la discrepanza con Coinglass
- Geometria del modello: dopo −15% in tre settimane gli short aperti più in alto a 10–25x hanno la liquidazione a +10–20%, i long
  rimasti a bassa leva l'hanno a −5–10%: entro ±5% pesano i long; entro ±15% la nostra mappa ha già 528 M$ short contro 193 M$ long
  (stessa direzione di Coinglass, scala ~3–6 volte più piccola).
- La cascata del 13/11 ha tolto l'11% dell'OI (7,24 → 6,45 B$, ore stimate con OKX): nel modello ogni calo di OI riduce in
  proporzione tutte le posizioni, anche gli short sopra. Coinglass usa un modello proprietario (volume, leve, nessuna chiusura
  dichiarata) che non si può verificare.
- I soli livelli VERI disponibili (Hyperliquid, conti ≥ 1 M$, data/liqsnap, 29 fotografie 11–13/11) danno ragione alla nostra
  forma vicino al prezzo: entro ±5% short sopra 0% del totale (18–29 M$ long sotto, 0 short), entro ±10% 7–14% short
  (onchain.txt). Correlazione nel tempo con la quota short della mappa: v1 0,68 / v2 0,67 a ±10%.

## Decisione
v1 resta nel tool (radar/liqmap.py VERSION = 1, campo "v" nel risultato). La v2 è pronta (with_taker_share, okx_taker_hourly per
le ore dopo l'archivio, ripiego 50/50) ma non si accende. Le mappe stimate (nostra e Coinglass) restano contesto: il dato reale
sono gli eventi di liquidazione (data/liq_events, data/liq_stream con radar/liqstream.py) e i livelli on-chain.
Nota dati: nella cache dello studio (h.pkl) manca il giorno 2026-10-28 delle candele 1h archiviate; il tool usa le candele spot
data-api e non ne risente.

## File
v2_data.py (dati) · v2_valid.py (M1, M2, placebo, novembre) · v2_onchain.py (forma contro Hyperliquid/Lighter) · v2_oggi.py (13/11)
· risultati.txt, onchain.txt, oggi.txt, giorni_*.csv, onchain.csv.
