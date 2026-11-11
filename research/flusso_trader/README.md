# Flusso perp vs spot ("lo spot assorbe") · 11/11/2026 · VERDETTO: SOLO CONTESTO
Script: run.py (output: out.txt). Regole e soglie in PREREG.md, scritte prima dei risultati.

## 1. Riproduzione dei numeri del trader
Binance BTCUSDT perp giornaliero (UTC), quota taker buy: 10/11 **48,3%** su 12,4 mld $ (delta −5.832 BTC), spot 10/11 delta +471 BTC
(sf5z +1,48). Il trader: 49,35% su 10,98 mld $. Direzione uguale (perp vende, spot compra), cifre diverse: finestra/giorno diversi
(probabile 11/11 parziale o fuso non UTC); i dati perp orari dell'11/11 non sono ancora nell'archivio.
Ultimi 10 giorni quota perp: 51,3 · 50,4 · 49,8 · 51,4 · 49,2 · 49,4 · 46,3 · 49,1 · 50,9 · 48,3%.

## 2. Test dal 01/01/2021 (eventi, eccesso di rendimento in pp vs media incondizionata; base 7 g = +0,57%)
| var | n | +1g | +3g | +7g | +14g | p placebo 7g | 7g 21–23 | 7g 24→ | 10k long 7g | senza migliore |
|---|---|---|---|---|---|---|---|---|---|---|
| V1 N5 riequil. | 31 | +0,5 | +2,7 | +2,9 | +1,9 | 0,03 | +3,2 | +2,6 | 23,5k | 17,3k |
| V2 N3 | 39 | −0,1 | +1,4 | +1,5 | +1,7 | 0,12 | +1,8 | +1,2 | 17,6k | 13,0k |
| V3 N7 | 31 | +0,7 | +1,7 | +0,7 | +1,6 | 0,32 | −2,6 | +3,7 | 12,7k | 10,4k |
| V4 zA −0,75 | 47 | +0,3 | +1,2 | +1,2 | +1,3 | 0,15 | +0,2 | +2,0 | 17,5k | 12,9k |
| V5 zA −1,25 | 18 | −0,6 | +0,2 | −1,9 | −0,9 | 0,84 | −3,5 | +0,6 | 7,4k | 6,0k |
| V6 N5 severa (>50,5%) | 25 | +0,3 | +2,0 | +3,1 | +1,2 | 0,03 | +2,7 | +3,4 | 20,5k | 15,6k |
| V7 N3 severa | 29 | +0,8 | +1,8 | +1,8 | +2,2 | 0,11 | +2,6 | +1,1 | 16,5k | 12,5k |
| V8 N7 severa | 28 | +0,2 | +1,1 | +1,9 | +1,2 | 0,10 | −0,4 | +3,9 | 17,3k | 13,8k |
Riferimenti: buy & hold 25,2k; W3 78,5k (DD −21%).
Lettura: segno quasi sempre positivo, ma solo V1 e V6 passano p<0,05 (non corretto per 8 prove) e i vicini (V3, V5) cadono:
risultato a gradino. La versione severa non è più forte di quella base. Nessuna variante batte il buy & hold come trade a sé.

## 3. Rapporto con W3
Ingressi W3 (13) preceduti da un evento nei 14 giorni: 1–3 per variante, contro 1,5–3,7 attesi a caso. Nessun preavviso utile;
W3 usa già pf14z, che contiene la stessa informazione su scala più lenta.

## 4. Stato di oggi (chiusura 10/11)
Stato A non attivo (pz5 −0,65, sz5 +1,48: perp in vendita moderata, spot positivo). Ultimi eventi: V1 03/11, V6 04/11.
Da guardare come contesto: un nuovo stato A (pz5 < −1 con spot ≥ 0) seguito da quota perp > 50,5%.

## Lezione proposta per RESEARCH.md
"Divergenza giornaliera perp in vendita / spot che assorbe, poi riequilibrio (11/11): +1–3 pp a 7 g, ma significativo solo in 2/8
varianti, vicini incoerenti, nessun preavviso sugli ingressi W3. Solo contesto; non riproporre senza dati nuovi (es. CVD multi-exchange)."
