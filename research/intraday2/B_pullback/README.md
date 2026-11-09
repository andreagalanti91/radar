# Famiglia B · Pullback nel trend 1h (BTC, ETH, SOL) — esito: NESSUNA variante passa

Regole e soglie: `PREREG.md` (scritto prima dei risultati). Codice: `pullback.py` (`is` = scelta sul 2021–23, `oos` = giudizio,
placebo 500 giri, vicini). Dati: `is_results.csv`, `oos_results.csv`, `trades_B5.csv` (la meno peggio sul 2021–23).
Impostazione: 10.000 $, rischio 1%/trade, leva di margine 2x, uscite di riferimento del PIANO (stop 1,5 ATR 1h, TP1 1,5R metà,
pareggio, TP2 3R, 48 barre), costi e funding reali, stessi parametri sui 3 asset, long e short.

| id | regola (long; short specchio) | 10k → $ (2021→) | rend. | DD max | trade/mese | WR | PF | exp R | MAR | IS rend./PF/R | OOS rend./PF/R | asset OOS + | placebo pct | vicini (med.) |
|---|---|---|---|---|---|---|---|---|---|---|---|---|---|---|
| B1 | ritest EMA20 4h + candela di rifiuto, ADX>20 | 4.949 | −50,5% | −52,6% | 8,1 | 39,5% | 0,80 | −0,13 | −0,22 | −35,8% / 0,78 / −0,15 | −23,0% / 0,83 / −0,10 | 1/3 | 73 | −26,2% |
| B2 | ritest EMA50 4h + rifiuto | 6.949 | −30,5% | −43,0% | 3,6 | 38,4% | 0,75 | −0,16 | −0,14 | −29,0% / 0,63 / −0,28 | −2,1% / 0,97 / −0,01 | 2/3 | 85 | −3,2% |
| B3 | RSI(2) < 10 sopra EMA50 4h | 2.173 | −78,3% | −83,0% | 25,1 | 41,2% | 0,89 | −0,09 | −0,28 | −36,7% / 0,93 / −0,05 | −65,7% / 0,78 / −0,14 | 0/3 | 56 | −64,2% |
| B4 | RSI(14) risale sopra 40 dopo < 32 | 5.310 | −46,9% | −48,9% | 5,0 | 36,7% | 0,73 | −0,20 | −0,21 | −24,1% / 0,75 / −0,17 | −30,0% / 0,71 / −0,23 | 1/3 | 19 | −24,7% |
| B5 | ritest VWAP di sessione, 12–20 UTC | 7.082 | −29,2% | −54,4% | 10,8 | 44,2% | 0,94 | −0,05 | −0,11 | +20,0% / 1,07 / +0,05 | −41,0% / 0,74 / −0,15 | 0/3 | 48 | −38,2% |
| B6 | ritest dopo rottura Donchian 20 4h | 1.560 | −84,4% | −84,9% | 15,2 | 37,9% | 0,73 | −0,18 | −0,32 | −62,9% / 0,72 / −0,19 | −58,0% / 0,75 / −0,18 | 0/3 | 18 | −56,5% |
| B7 | B1 + ADX>25, ATR% 20–80° pct, 7–21 UTC | 6.691 | −33,1% | −39,7% | 2,6 | 36,5% | 0,65 | −0,25 | −0,17 | −17,6% / 0,68 / −0,24 | −18,7% / 0,62 / −0,25 | 0/3 | 27 | −19,6% |
| B8 | B3 + filtri severi di B7 | 4.503 | −55,0% | −61,6% | 10,8 | 40,6% | 0,84 | −0,11 | −0,21 | −27,2% / 0,87 / −0,08 | −38,1% / 0,78 / −0,14 | 0/3 | 54 | −34,7% |
| B&H | 1/3 BTC, ETH, SOL a 1x | 213.432 | +2.034% | −95,2% | – | – | – | – | – | +2.258% | +21,3% (DD −62%) | – | – | – |
| W2+MACD | BTC settimanale, 1x (RESEARCH.md) | ~118.900 | ~+1.089% | −22,7% | 0,2 | 93% | – | – | – | – | – | – | – | – |

Placebo e vicini sono calcolati sul 2024→oggi (criteri del PIANO). Senza il trade migliore il 2024→oggi resta negativo per tutte.

**Scelta sul 2021–23**: nessuna variante supera il filtro preregistrato (2–12 trade/mese, PF ≥ 1,2, aspettativa > 0). La migliore,
B5, ha PF 1,07 e +0,05R, solo 2021–22 positivi (2023 −10%), solo short e SOL in utile. Fuori campione crolla (−41%, PF 0,74).
**Costi**: senza commissioni, slippage e funding l'aspettativa sul 2021–23 salirebbe di circa 0,11–0,13R a trade (B5 +0,18R, B3
+0,06R, le altre restano negative): anche senza attriti l'edge lordo è nullo o quasi, e i costi lo azzerano.
**Pochi trade non bastano**: i filtri severi (B7) portano a 2,6 trade/mese ma peggiorano l'aspettativa (−0,25R): il filtro
taglia trade a caso, non i cattivi.

**Verdetto**: famiglia B BOCCIATA. Nessuna variante va in fase D (uscite/leva) né nel tool.

**Lezione proposta per RESEARCH.md**: «Pullback nel trend su 1h (ritest EMA20/50 4h con candela di rifiuto, RSI(2)/RSI(14)
in ipervenduto nel trend, VWAP di sessione, ritest dopo rottura 4h; con e senza filtri ADX/volatilità/sessione) su BTC/ETH/SOL
dal 2021 con uscite PIANO: 8 varianti su 8 negative fuori campione (PF 0,62–0,97, −0,01/−0,25R), nessuna sopra il 90° pct
del placebo; l'edge lordo è ≤ 0,18R e i costi ne mangiano 0,12R. Conferma la lezione 78: su 1h comprare il ritracciamento nel
trend non batte i costi, e filtrare per avere pochi trade non crea qualità. Non riproporre senza un'informazione nuova (flusso,
derivati) che separi i pullback buoni dai cattivi.»
