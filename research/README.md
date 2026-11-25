# Ricerca · indice degli studi

Una cartella per studio. Dove c'è, si legge prima il `README.md` (o `REPORT.md`): verdetto in testa, poi numeri, controlli e
deviazioni. `PREREG.md` è la preregistrazione, committata da sola prima di qualsiasi rendimento. Le lezioni numerate sono in
[`../RESEARCH.md`](../RESEARCH.md); il riassunto per una nuova sessione in [`../memoria/02-ricerca/INDICE.md`](../memoria/02-ricerca/INDICE.md).

**Conclusione generale:** dal 2021 solo il trend settimanale (W3.1) regge su BTC; tutto il resto è contesto. Riferimento per
ogni confronto: W3.1 dal 01/01/2021, 10.000 → 27.190 $, drawdown −9,8%, 13 trade.

## Strategia in uso (W2 → W3 → W3.1)

| Cartella | Contenuto | Esito |
|---|---|---|
| [`p2_nuovi`](p2_nuovi/REPORT.md) | rischio allo stop, griglia stop/TP, dati congelati usati dagli studi successivi | rischio 10% → **W3.1** |
| [`dirompente`](dirompente/) | avvocato del diavolo su W3 | 25% di rischio troppo alto (lezione 99) |
| [`ingressi_uscite`](ingressi_uscite/README.md) | DCA, uscite a scaglioni, TP, stop, distribuzione, 7 giorni di decisione | nessuna variante batte W3.1 (105) |
| [`sfida_w3`](sfida_w3/REPORT.md) | sfida a W2 + MACD | nasce W3 |
| [`w2_robustezza`](w2_robustezza/README.md) · [`w2_migliorie`](w2_migliorie/README.md) | robustezza statistica e migliorie M1–M10 | nessuna regola da adottare |
| [`perdita_2026`](perdita_2026/PREREG.md) | analisi della perdita del 2026 | vedi `LOSERS.md` |
| [`notte_1511`](notte_1511/REPORT.md) | giorno di decisione, swing 2–3 giorni, macro, probabilità, S/R | domenica per convenzione (94), swing 0/32 (95) |
| [`preview`](preview/) · [`piani`](piani/) | dati della Pre-analisi, piano settimanale di esempio | strumenti |

## Swing e supporti/resistenze

| Cartella | Contenuto | Esito |
|---|---|---|
| [`swing_sr`](swing_sr/README.md) | swing su S/R settimanali, stop 5–10%, TP 10–15% su BTC, 70/30 con W3.1 | non valida, 0/405 sopra W3.1 (106) |
| [`swing_sr_multi`](swing_sr_multi/README.md) | stessa strategia su 15 asset (indici, oro, argento, petrolio, azioni) | 0/15 validi (107) |
| [`nuova_strategia`](nuova_strategia/REPORT.md) | settimanale/mensile con volumi e S/R | non funziona fuori campione |
| [`sr_volume`](sr_volume/) · [`argento`](argento/) · [`brent`](brent/) | S/R con volume, ritest di supporto rotto | nessun vantaggio (75–77) |
| [`ta_settimanale`](ta_settimanale/README.md) · [`censimento`](censimento/REPORT.md) | analisi tecnica settimanale/mensile, 15 indicatori comuni | contesto |
| [`indicatori_tv`](indicatori_tv/) · [`zeiierman`](zeiierman/REPORT.md) · [`macd_flip`](macd_flip/README.md) | indicatori TradingView, Trend Pressure, MACD flip | nessun vantaggio (38, 79, 86, 91) |

## Order book, liquidazioni, market maker

| Cartella | Contenuto | Esito |
|---|---|---|
| [`book_sentiment`](book_sentiment/README.md) | sentiment da book + liquidazioni (pagina Book) | descrittivo, 0/14; rifare febbraio 2027 (108) |
| [`book_liq`](book_liq/README.md) | book e liquidazioni come supporto a W3.1 (15 giorni) | nessun supporto; rifare 20/12 e marzo 2027 |
| [`mm_assorbimento`](mm_assorbimento/README.md) | assorbimento e compressione dei market maker | respinto (98) |
| [`liquidazioni`](liquidazioni/README.md) · [`liq_fasce`](liq_fasce/README.md) · [`liq_squeeze`](liq_squeeze/README.md) · [`liqmap_v2`](liqmap_v2/README.md) | calamita, fasce, squeeze, mappa v2 | nessun vantaggio (72, 81, 92, 93) |
| [`liq_fonti`](liq_fonti/README.md) · [`liq_onchain`](liq_onchain/PREREG.md) | censimento fonti, livelli on-chain | strumenti |
| [`flusso_trader`](flusso_trader/README.md) | flusso perp contro spot | solo contesto |

## Altri mercati e altre idee

| Cartella | Contenuto | Esito |
|---|---|---|
| [`w32_asset2`](w32_asset2/README.md) | W3.2 su top 200 crypto (oggi e 2020) e top 100 azioni dal 2020, cancello BTC, screener annuale, SOL e TAO | non si trasferisce; TRX solo in osservazione (123) |
| [`peso_btc_eth`](peso_btc_eth/README.md) | peso del capitale fra BTC ed ETH con W3.2 | 50/50 resta; 100/0 non promosso (124) |
| [`utxo_pl`](utxo_pl/README.md) | indicatore UTXO P/L (CryptoQuant, sostituto MVRV) come supporto a W3.2 | no come regola, solo contesto (125) |
| [`v1_confronto`](v1_confronto/README.md) | strategia v1 dell'utente (voto di 17 indicatori) contro W3.2 | W3.2 migliore; v1 solo come confronto (126) |
| [`multi_asset`](multi_asset/README.md) · [`ema200_vix`](ema200_vix/LOGICA.md) | W3.1 solo prezzo su 13 asset, EMA200 + VIX | non si trasferisce (104) |
| [`top50`](top50/) · [`top10_w3`](top10_w3/README.md) · [`w2_alt`](w2_alt/) | W2/W3 su altre crypto e indici | solo BTC (74) |
| [`short_w2`](short_w2/README.md) | strategie short dedicate | non promosse (80) |
| [`intraday`](intraday/) · [`intraday2`](intraday2/README.md) | intraday 1h/4h | rimosso dal tool (78, 82) |
| [`chento`](chento/README.md) | trader seguito | registro dei segnali (90) |
| [`scout`](scout/PREREG.md) | criteri delle balene Hyperliquid | in uso nella sezione Wallet (in pausa) |
| [`opzioni_studio`](opzioni_studio/README.md) · [`opzioni_sim`](opzioni_sim/README.md) · [`opzioni_import`](opzioni_import/OPZIONI_W32.md) | opzioni su BTC con i segnali di W3.2: struttura, uscite, segnali indipendenti; spesa per operazione; studio e modulo dell'utente | le 7 regole restano, nessun segnale in più (122) |

## File sciolti

`LOSERS.md` (trade persi e pattern), `LIVE_PAPER.md`, `weekly_w3_trades.csv` (trade di riferimento di W3) e i CSV `weekly_*`,
`ta_*`, `ichimoku_*` dei vecchi confronti W2, citati in `RESEARCH.md`.
