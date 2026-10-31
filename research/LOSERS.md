# Registro dei trade in stop di v2 (rischio base 4,67%, dal 2022-03, solo BTC)

Fonte: research/losers.csv (tutte le colonne) (105 trade v2). R = distanza TP–medio.
MFE/MAE in R dal prezzo di ingresso fino alla barra di stop; "dopo" = 7 giorni (42 barre 4h) dallo stop; "stop +k ATR" = il TP
sarebbe arrivato prima di uno stop più largo di k ATR (entro 7 giorni)?

Dei 7 trade segnalati dall'utente, in v2 **2022-08-19 sflow short (+3,87%) e 2025-04-07 sflow short (+2,11%) sono TP**: con la conferma 4h
e il TP a 1R non sono più perdite. Gli altri 5 sono qui sotto (segnati con *).

## * 2022-04-23 · fundneg · long · -3.50% del conto (rischio 3.47%)
- Regime: W-SMA40 sotto, SMA50 sotto, SMA200 sotto, trend 4h misto; vol bassa sì
- Ingresso 2022-04-25 20:00:00 (lun): pf14z 0.06, DT spot/perp 0.084/0.064, funding_z -1.06, ls_z 1.76, d SMA20 4h 0.43 ATR, RSI 4h 54.8, %B 4h 0.97; 7 g prima -1.1%
- Stop dopo 24h, entrambi i livelli riempiti; MFE 0.48R, MAE -2.02R
- Dopo lo stop: 3 g +0.2%, 7 g -2.1% (nel verso del trade); massimo favorevole 0.54R dal medio; oltre lo stop di 0.68 ATR; stop +0,5 ATR → stop_largo, +1 ATR → no
- Contesto: Fine aprile 2022: mercato in calo verso il crollo LUNA/UST (9–12/05). Rimbalzo long fallito in 24h.
- Causa probabile: Long contro trend (sotto W-SMA40, sotto SMA50/200) in bear market; MFE 0,48R poi giù.
- Regola: Già ×0,6 dalla W-SMA40. Nessuna regola testata lo evita; tetto 3–4% non incide (rischio 3,5%).

## 2022-06-13 · capit · long · -2.43% del conto (rischio 2.42%)
- Regime: W-SMA40 sotto, SMA50 sotto, SMA200 sotto, trend 4h giu; vol bassa no
- Ingresso 2022-06-16 00:00:00 (gio): pf14z -0.4, DT spot/perp 0.029/0.044, funding_z -0.05, ls_z -0.01, d SMA20 4h -0.23 ATR, RSI 4h 39.6, %B 4h 0.44; 7 g prima -25.2%
- Stop dopo 16h, entrambi i livelli riempiti; MFE 0.33R, MAE -1.46R
- Dopo lo stop: 3 g -3.1%, 7 g +0.7% (nel verso del trade); massimo favorevole -0.25R dal medio; oltre lo stop di 1.74 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: 13/06/2022 blocco prelievi Celsius / crisi 3AC: BTC −25% nei 7 giorni prima, poi 17,6k il 18/06.
- Causa probabile: Long "capitolazione" troppo presto dentro un crollo da insolvenza.
- Regola: Nessuna; rischio già basso (2,4%).

## 2022-08-27 · sflow · short · -5.21% del conto (rischio 5.1%)
- Regime: W-SMA40 sotto, SMA50 sotto, SMA200 sotto, trend 4h giu; vol bassa sì
- Ingresso 2022-08-29 00:00:00 (lun): pf14z -1.17, DT spot/perp 0.024/0.095, funding_z -1.85, ls_z 0.51, d SMA20 4h -0.93 ATR, RSI 4h 20.5, %B 4h 0.15; 7 g prima -9.1%
- Stop dopo 32h, entrambi i livelli riempiti; MFE 0.01R, MAE -1.48R
- Dopo lo stop: 3 g +2.2%, 7 g +3.0% (nel verso del trade); massimo favorevole 0.43R dal medio; oltre lo stop di -0.02 ATR; stop +0,5 ATR → no, +1 ATR → no
- Contesto: Dopo il discorso di Powell a Jackson Hole (26/08/2022): short dopo il calo, rimbalzo.
- Causa probabile: Short ipervenduto (RSI 4h 20,5, %B 0,15): vendita in fondo al movimento.
- Regola: Tetto 4% (5,1% → ~4%); RSI 4h estremo per gli short (da testare).

## 2022-09-16 · capit · long · -2.29% del conto (rischio 2.26%)
- Regime: W-SMA40 sotto, SMA50 sotto, SMA200 sotto, trend 4h giu; vol bassa sì
- Ingresso 2022-09-17 04:00:00 (sab): pf14z 0.32, DT spot/perp 0.006/0.055, funding_z 0.7, ls_z 1.24, d SMA20 4h -0.08 ATR, RSI 4h 41.7, %B 4h 0.42; 7 g prima -6.7%
- Stop dopo 48h, entrambi i livelli riempiti; MFE 0.44R, MAE -1.76R
- Dopo lo stop: 3 g +0.2%, 7 g +0.1% (nel verso del trade); massimo favorevole 0.53R dal medio; oltre lo stop di 0.78 ATR; stop +0,5 ATR → stop_largo, +1 ATR → no
- Contesto: Dopo il Merge (15/09) e prima del FOMC +75 pb (21/09/2022).
- Causa probabile: Long contro trend in bear market; MFE 0,44R.
- Regola: Nessuna testata.

## 2022-10-04 · flow · long · -2.76% del conto (rischio 2.69%)
- Regime: W-SMA40 sotto, SMA50 sopra, SMA200 sotto, trend 4h su; vol bassa sì
- Ingresso 2022-10-05 00:00:00 (mer): pf14z 0.88, DT spot/perp 0.04/0.052, funding_z 0.99, ls_z -1.23, d SMA20 4h 0.91 ATR, RSI 4h 74.0, %B 4h 1.03; 7 g prima +6.6%
- Stop dopo 68h, entrambi i livelli riempiti; MFE 0.19R, MAE -1.6R
- Dopo lo stop: 3 g -1.5%, 7 g -1.3% (nel verso del trade); massimo favorevole -0.19R dal medio; oltre lo stop di 1.36 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Rimbalzo di inizio ottobre 2022 respinto prima del CPI del 13/10.
- Causa probabile: Long ipercomprato (RSI 4h 74, %B 1,03) sotto la W-SMA40.
- Regola: Nessuna testata; lez. 26 dice che per i long l'ipercomprato non è peggiore (qui RSI<70 non aiuta).

## 2022-10-19 · sflow · short · -3.74% del conto (rischio 3.74%)
- Regime: W-SMA40 sotto, SMA50 sotto, SMA200 sotto, trend 4h misto; vol bassa sì
- Ingresso 2022-10-20 04:00:00 (gio): pf14z -1.81, DT spot/perp 0.025/0.036, funding_z 0.71, ls_z 0.63, d SMA20 4h -0.46 ATR, RSI 4h 38.5, %B 4h 0.06; 7 g prima -0.2%
- Stop dopo 132h, entrambi i livelli riempiti; MFE 0.86R, MAE -1.67R
- Dopo lo stop: 3 g -4.6%, 7 g -3.8% (nel verso del trade); massimo favorevole -1.06R dal medio; oltre lo stop di 2.12 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Fine ottobre 2022: short squeeze 25–26/10 (19k → 20,8k).
- Causa probabile: Short in bassa volatilità, durato 132h; MFE 0,86R (quasi a TP) poi squeeze.
- Regola: Nessuna (il TP di salvataggio a 0,5R dopo il 2° livello è stato testato: peggiora).

## 2022-11-05 · flow · long · -2.42% del conto (rischio 2.36%)
- Regime: W-SMA40 sotto, SMA50 sopra, SMA200 sotto, trend 4h misto; vol bassa sì
- Ingresso 2022-11-07 20:00:00 (lun): pf14z 0.13, DT spot/perp -0.001/0.069, funding_z -0.42, ls_z -1.51, d SMA20 4h -0.42 ATR, RSI 4h 48.2, %B 4h 0.24; 7 g prima +2.3%
- Stop dopo 8h, entrambi i livelli riempiti; MFE 0.1R, MAE -1.67R
- Dopo lo stop: 3 g -13.9%, 7 g -16.7% (nel verso del trade); massimo favorevole 0.08R dal medio; oltre lo stop di 7.39 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Crollo FTX (8–9/11/2022): −13,9% nei 3 giorni dopo lo stop.
- Causa probabile: Evento di insolvenza: imprevedibile dal flusso.
- Regola: Nessuna: lo stop ha fatto il suo lavoro (stop più largo = perdita peggiore).

## * 2022-12-28 · sflow · short · -3.56% del conto (rischio 3.6%)
- Regime: W-SMA40 sotto, SMA50 sotto, SMA200 sotto, trend 4h giu; vol bassa sì
- Ingresso 2022-12-29 00:00:00 (gio): pf14z -1.57, DT spot/perp -0.01/0.064, funding_z 0.35, ls_z 1.01, d SMA20 4h -0.55 ATR, RSI 4h 31.4, %B 4h 0.03; 7 g prima -1.6%
- Stop dopo 164h, entrambi i livelli riempiti; MFE 0.77R, MAE -1.6R
- Dopo lo stop: 3 g -0.0%, 7 g -5.9% (nel verso del trade); massimo favorevole -0.07R dal medio; oltre lo stop di 1.59 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Fine dicembre 2022, volatilità minima; inizio del rally di gennaio 2023.
- Causa probabile: Short in bassa volatilità al minimo del ciclo (pf14z −1,57: venditori già esauriti).
- Regola: Nessuna testata; candidato: niente short con vol bassa + pf14z molto negativo.

## 2023-04-13 · flow · long · -3.48% del conto (rischio 3.36%)
- Regime: W-SMA40 sopra, SMA50 sopra, SMA200 sopra, trend 4h su; vol bassa sì
- Ingresso 2023-04-14 04:00:00 (ven): pf14z 0.26, DT spot/perp -0.002/0.045, funding_z -0.02, ls_z -1.32, d SMA20 4h 0.59 ATR, RSI 4h 76.4, %B 4h 1.12; 7 g prima +9.5%
- Stop dopo 80h, entrambi i livelli riempiti; MFE 0.45R, MAE -1.92R
- Dopo lo stop: 3 g -4.0%, 7 g -8.2% (nel verso del trade); massimo favorevole 0.12R dal medio; oltre lo stop di 2.61 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Massimo di metà aprile 2023 (~31k) e ritracciamento.
- Causa probabile: Long ipercomprato su breakout di un massimo locale (RSI 4h 76).
- Regola: Nessuna testata.

## 2023-08-18 · capit · long · -5.51% del conto (rischio 5.45%)
- Regime: W-SMA40 sopra, SMA50 sotto, SMA200 sotto, trend 4h giu; vol bassa sì
- Ingresso 2023-08-19 16:00:00 (sab): pf14z -2.12, DT spot/perp 0.108/0.025, funding_z 1.34, ls_z 1.14, d SMA20 4h -1.36 ATR, RSI 4h 21.8, %B 4h 0.29; 7 g prima -10.9%
- Stop dopo 80h, entrambi i livelli riempiti; MFE 0.15R, MAE -1.66R
- Dopo lo stop: 3 g +2.6%, 7 g +7.7% (nel verso del trade); massimo favorevole 3.9R dal medio; oltre lo stop di -0.45 ATR; stop +0,5 ATR → TP, +1 ATR → TP
- Contesto: Flash crash del 17/08/2023 (29k → 25k); long il giorno dopo, poi TP con stop più largo.
- Causa probabile: Rimbalzo dopo crollo: stop 1 ATR troppo stretto nel picco di volatilità (falso stop).
- Regola: Stop +0,5/+1 ATR → TP, ma lez. 4: stop più largo = perdita maggiore negli altri casi.

## 2023-11-09 · flow · long · -6.07% del conto (rischio 5.71%)
- Regime: W-SMA40 sopra, SMA50 sopra, SMA200 sopra, trend 4h su; vol bassa sì
- Ingresso 2023-11-10 12:00:00 (ven): pf14z 0.02, DT spot/perp 0.109/0.035, funding_z 1.7, ls_z -1.5, d SMA20 4h 1.03 ATR, RSI 4h 67.1, %B 4h 0.87; 7 g prima +8.2%
- Stop dopo 100h, entrambi i livelli riempiti; MFE 0.57R, MAE -1.47R
- Dopo lo stop: 3 g +1.1%, 7 g +3.0% (nel verso del trade); massimo favorevole 1.54R dal medio; oltre lo stop di 0.97 ATR; stop +0,5 ATR → stop_largo, +1 ATR → TP
- Contesto: Spike e ritracciamento del 9–10/11/2023 (notizie ETF). Perdita peggiore (−6,07%), rischio 5,71% per DT alto.
- Causa probabile: Delta taker forte su uno spike di notizie: peso alto proprio sul trade che fa un falso movimento.
- Regola: Tetto 4% (−6,1 → −4,0); stop +1 ATR → TP.

## 2024-02-14 · brk · long · -4.44% del conto (rischio 4.28%)
- Regime: W-SMA40 sopra, SMA50 sopra, SMA200 sopra, trend 4h su; vol bassa sì
- Ingresso 2024-02-15 04:00:00 (gio): pf14z 1.26, DT spot/perp 0.049/0.034, funding_z 0.06, ls_z -1.31, d SMA20 4h 1.49 ATR, RSI 4h 76.9, %B 4h 0.97; 7 g prima +17.5%
- Stop dopo 60h, entrambi i livelli riempiti; MFE 0.41R, MAE -1.48R
- Dopo lo stop: 3 g +2.8%, 7 g +1.7% (nel verso del trade); massimo favorevole 0.97R dal medio; oltre lo stop di 0.1 ATR; stop +0,5 ATR → no, +1 ATR → no
- Contesto: Rally ETF di febbraio 2024, CPI del 13/02; poi salita lenta.
- Causa probabile: Long su breakout molto esteso (+17,5% nei 7 giorni, d SMA20 1,49 ATR, RSI 77).
- Regola: Tetto 4–4,5%; candidato: peso ridotto con estensione > 1,2 ATR dalla SMA20 4h.

## 2024-07-19 · brk · long · -3.40% del conto (rischio 3.3%)
- Regime: W-SMA40 sopra, SMA50 sopra, SMA200 sopra, trend 4h su; vol bassa no
- Ingresso 2024-07-20 16:00:00 (sab): pf14z 2.31, DT spot/perp 0.01/0.032, funding_z -0.86, ls_z -0.76, d SMA20 4h 0.68 ATR, RSI 4h 66.2, %B 4h 0.86; 7 g prima +13.6%
- Stop dopo 108h, entrambi i livelli riempiti; MFE 0.92R, MAE -1.66R
- Dopo lo stop: 3 g +5.1%, 7 g +0.1% (nel verso del trade); massimo favorevole 2.24R dal medio; oltre lo stop di 0.31 ATR; stop +0,5 ATR → TP, +1 ATR → TP
- Contesto: Rally pre-conferenza Bitcoin di Nashville; TP con stop più largo.
- Causa probabile: Falso stop (MFE 0,92R prima dello stop).
- Regola: Stop +0,5 ATR → TP (non generalizzabile).

## * 2024-07-28 · brk · long · -5.82% del conto (rischio 5.74%)
- Regime: W-SMA40 sopra, SMA50 sopra, SMA200 sopra, trend 4h su; vol bassa no
- Ingresso 2024-07-29 04:00:00 (lun): pf14z 1.26, DT spot/perp 0.082/0.064, funding_z -0.5, ls_z -0.94, d SMA20 4h 0.65 ATR, RSI 4h 67.8, %B 4h 1.03; 7 g prima +2.2%
- Stop dopo 16h, entrambi i livelli riempiti; MFE 0.44R, MAE -1.77R
- Dopo lo stop: 3 g -2.4%, 7 g -19.4% (nel verso del trade); massimo favorevole -0.67R dal medio; oltre lo stop di 7.59 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Conferenza di Nashville (discorso di Trump 27/07/2024): "sell the news", poi crollo del 5/08 (carry trade sullo yen): −19% in 7 giorni.
- Causa probabile: Breakout "da notizia" con DT alto (rischio 5,74%) e subito il crollo macro.
- Regola: Tetto 4% (−5,8 → −4,0). Nessun filtro lo evita.

## 2024-09-05 · sflow · short · -5.71% del conto (rischio 5.61%)
- Regime: W-SMA40 sotto, SMA50 sotto, SMA200 sotto, trend 4h giu; vol bassa no
- Ingresso 2024-09-06 16:00:00 (ven): pf14z -0.17, DT spot/perp 0.095/0.045, funding_z -0.8, ls_z 1.49, d SMA20 4h -1.12 ATR, RSI 4h 27.6, %B 4h -0.14; 7 g prima -7.0%
- Stop dopo 76h, entrambi i livelli riempiti; MFE 0.84R, MAE -1.75R
- Dopo lo stop: 3 g -2.7%, 7 g -2.9% (nel verso del trade); massimo favorevole -0.43R dal medio; oltre lo stop di 1.59 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Inizio settembre 2024 (NFP del 6/09), poi rally verso il taglio Fed di 50 pb (18/09).
- Causa probabile: Short ipervenduto (RSI 27,6, %B −0,14) con DT alto (rischio 5,6%).
- Regola: Tetto 4%; candidato: peso ridotto sugli short con %B 4h < 0.

## 2024-09-14 · flow · long · -1.42% del conto (rischio 1.4%)
- Regime: W-SMA40 sotto, SMA50 sopra, SMA200 sotto, trend 4h su; vol bassa no
- Ingresso 2024-09-15 04:00:00 (dom): pf14z 0.18, DT spot/perp -0.06/0.052, funding_z -1.62, ls_z -1.36, d SMA20 4h 0.5 ATR, RSI 4h 65.2, %B 4h 0.77; 7 g prima +10.6%
- Stop dopo 36h, entrambi i livelli riempiti; MFE 0.15R, MAE -1.57R
- Dopo lo stop: 3 g +9.5%, 7 g +9.5% (nel verso del trade); massimo favorevole 3.2R dal medio; oltre lo stop di 0.12 ATR; stop +0,5 ATR → TP, +1 ATR → TP
- Contesto: Prima del taglio Fed (18/09/2024): falso stop, poi +9,5%.
- Causa probabile: Stop in bassa liquidità del weekend (domenica), DT spot contrario (−0,06).
- Regola: Stop +0,5 ATR → TP; rischio già minimo (1,4%).

## * 2024-12-17 · flow · long · -2.80% del conto (rischio 2.76%)
- Regime: W-SMA40 sopra, SMA50 sopra, SMA200 sopra, trend 4h giu; vol bassa sì
- Ingresso 2024-12-19 12:00:00 (gio): pf14z 0.46, DT spot/perp 0.026/-0.007, funding_z 0.39, ls_z -1.19, d SMA20 4h -0.57 ATR, RSI 4h 45.0, %B 4h 0.23; 7 g prima +2.1%
- Stop dopo 8h, entrambi i livelli riempiti; MFE 0.13R, MAE -2.25R
- Dopo lo stop: 3 g -3.4%, 7 g -2.8% (nel verso del trade); massimo favorevole -0.49R dal medio; oltre lo stop di 1.59 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: FOMC "hawkish" del 18/12/2024: 108k → 92k.
- Causa probabile: Evento macro programmato entro 24h dall'ingresso.
- Regola: Candidato: size ridotta nelle 48h prima del FOMC (calendario, da testare).

## 2025-03-08 · capit · long · -4.64% del conto (rischio 4.61%)
- Regime: W-SMA40 sopra, SMA50 sotto, SMA200 sopra, trend 4h giu; vol bassa no
- Ingresso 2025-03-10 12:00:00 (lun): pf14z -0.92, DT spot/perp 0.06/0.037, funding_z -1.29, ls_z 2.23, d SMA20 4h -0.39 ATR, RSI 4h 42.0, %B 4h 0.3; 7 g prima -9.9%
- Stop dopo 8h, entrambi i livelli riempiti; MFE 0.06R, MAE -1.85R
- Dopo lo stop: 3 g +2.9%, 7 g +6.6% (nel verso del trade); massimo favorevole 0.95R dal medio; oltre lo stop di 0.47 ATR; stop +0,5 ATR → no, +1 ATR → no
- Contesto: Summit cripto della Casa Bianca del 7/03/2025 (riserva strategica senza acquisti): delusione.
- Causa probabile: Long capitolazione sotto SMA50, crowd long (ls_z 2,23) e stop in 8h.
- Regola: Tetto 4% (−4,6 → −4,0); filtro affollamento ls_z (lez. 19: non robusto).

## 2025-03-24 · flow · long · -2.36% del conto (rischio 2.33%)
- Regime: W-SMA40 sopra, SMA50 sotto, SMA200 sopra, trend 4h su; vol bassa no
- Ingresso 2025-03-25 16:00:00 (mar): pf14z 1.43, DT spot/perp -0.118/-0.03, funding_z -1.2, ls_z -0.73, d SMA20 4h 0.49 ATR, RSI 4h 64.8, %B 4h 0.79; 7 g prima +7.6%
- Stop dopo 72h, entrambi i livelli riempiti; MFE 0.29R, MAE -1.47R
- Dopo lo stop: 3 g -1.9%, 7 g -0.1% (nel verso del trade); massimo favorevole 0.7R dal medio; oltre lo stop di 0.76 ATR; stop +0,5 ATR → stop_largo, +1 ATR → no
- Contesto: Fine marzo 2025, prima dei dazi del 2/04 ("Liberation Day").
- Causa probabile: Long con delta taker contrario (spot −0,12): rischio minimo.
- Regola: Nessuna; già al peso minimo.

## * 2026-02-01 · capit · long · -2.56% del conto (rischio 2.53%)
- Regime: W-SMA40 sotto, SMA50 sotto, SMA200 sotto, trend 4h giu; vol bassa no
- Ingresso 2026-02-02 16:00:00 (lun): pf14z -1.49, DT spot/perp 0.063/0.018, funding_z -0.23, ls_z 1.29, d SMA20 4h -0.37 ATR, RSI 4h 39.7, %B 4h 0.4; 7 g prima -10.0%
- Stop dopo 28h, entrambi i livelli riempiti; MFE 0.2R, MAE -2.68R
- Dopo lo stop: 3 g -6.8%, 7 g -9.1% (nel verso del trade); massimo favorevole -0.43R dal medio; oltre lo stop di 4.97 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Inizio febbraio 2026, fase ribassista sotto la W-SMA40 (−10% nei 7 giorni prima, poi −9% dopo lo stop); evento specifico non verificato.
- Causa probabile: Long capitolazione contro trend, MAE −2,7R (gap oltre lo stop).
- Regola: Già ×0,6; nessuna testata.

## 2026-07-22 · flow · long · -2.20% del conto (rischio 2.12%)
- Regime: W-SMA40 sotto, SMA50 sopra, SMA200 sotto, trend 4h misto; vol bassa sì
- Ingresso 2026-07-24 04:00:00 (ven): pf14z 0.85, DT spot/perp -0.0/0.052, funding_z 1.06, ls_z -0.73, d SMA20 4h -0.2 ATR, RSI 4h 50.8, %B 4h 0.33; 7 g prima +3.0%
- Stop dopo 92h, entrambi i livelli riempiti; MFE 0.28R, MAE -1.48R
- Dopo lo stop: 3 g +1.1%, 7 g +0.2% (nel verso del trade); massimo favorevole 0.37R dal medio; oltre lo stop di 0.78 ATR; stop +0,5 ATR → stop_largo, +1 ATR → no
- Contesto: Luglio 2026, laterale; evento non verificato.
- Causa probabile: Long sotto W-SMA40 con DT ~0: rischio minimo, stop lento (92h).
- Regola: Nessuna; già minimo.

## 2026-08-12 · sfund · short · -2.37% del conto (rischio 2.33%)
- Regime: W-SMA40 sotto, SMA50 sopra, SMA200 sotto, trend 4h giu; vol bassa sì
- Ingresso 2026-08-14 08:00:00 (ven): pf14z 0.25, DT spot/perp -0.084/0.073, funding_z 1.19, ls_z 0.58, d SMA20 4h -0.53 ATR, RSI 4h 33.8, %B 4h -0.02; 7 g prima -2.2%
- Stop dopo 84h, entrambi i livelli riempiti; MFE 0.4R, MAE -1.75R
- Dopo lo stop: 3 g -13.6%, 7 g -22.9% (nel verso del trade); massimo favorevole -0.75R dal medio; oltre lo stop di 11.39 ATR; stop +0,5 ATR → stop_largo, +1 ATR → stop_largo
- Contesto: Agosto 2026: squeeze rialzista (+23% in 7 giorni dopo lo stop); evento non verificato.
- Causa probabile: Short contro uno squeeze, DT spot contrario (−0,08).
- Regola: Nessuna; rischio già basso (2,3%).

## Pattern ricorrenti
1. **Tutti i 22 stop hanno riempito il 2° livello** (49 trade a 2 livelli: 27 TP, 22 stop, media +0,49% del conto; 56 trade a 1 livello: 56 TP, media +1,57%). La perdita nasce sempre dalla DCA completa (lezioni 1 e 15).
2. MFE mediana prima dello stop 0,29R (long): quasi tutti gli stop non sono mai andati in profitto; 4 su 22 (2023-08-18, 2023-11-09, 2024-07-19, 2024-09-14) sarebbero arrivati a TP con stop +1 ATR, 13 su 22 avrebbero preso anche lo stop più largo.
3. 6 su 22 sono legati a shock riconoscibili (Celsius 06/2022, Jackson Hole 08/2022, FTX 11/2022, flash crash 08/2023, carry trade 08/2024, FOMC 12/2024): il prezzo prosegue di 1,6–7,6 ATR oltre lo stop. Lo stop stretto qui ha limitato il danno.
4. Le perdite grandi (> 4,4%) sono i trade con DT alto (rischio 4,3–5,7%): ma il terzile alto del DT ha il tasso di stop più basso (14% contro 23–26%) e rende +2,0% medio contro +0,5–0,7%. Il peso paga: le perdite grandi sono il costo del peso, non un errore.
5. Short in stop: 4 su 26, tutti ipervenduti (RSI 4h 20–34, %B ≤ 0,15) o in bassa volatilità a fine ciclo (12/2022). Gli short in TP hanno RSI mediano 41,5: indizio (non testato) per gli short.
6. Nessuna differenza utile per W-SMA40 (59% degli stop sotto contro 53% dei TP), SMA50/200, ora o giorno (lunedì 6 stop/15, debole, n piccolo).

## Regole candidate (da testare con il gate, NON promosse)
- R1: peso v2 solo sulla 1ª tranche, 2ª tranche a peso neutro (riduce la perdita dei trade a DCA completa senza toccare i 56 TP a 1 livello).
- R2: calendario macro (FOMC/CPI/NFP): rischio ×0,5 se l'evento cade entro 48h dall'ingresso.
- R3: short con RSI 4h < 30 o %B 4h < 0 alla conferma: rischio ×0,6 (preregistrare, lez. 26 a U).
- R4: tetto al rischio 3,76% (perdita massima ~4%): già misurato in L1, costa ~45% del rendimento a 1x ma toglie la coda.
- Già bocciate in L1: failure stop 3/6 barre, 2° livello condizionato al DT, stop più stretto dopo il 2° livello, TP di salvataggio 0,5/0,75R, punteggio long.
## Aggiunte del giro 13 (31/10/2026)

7. **Correzione di una scheda**: lo stop del 2024-12-17 (flow long) NON ha il FOMC "entro 24h dopo l'ingresso": la decisione FOMC
   e' stata il 18/12/2024 alle 19:00 UTC, l'ingresso il 19/12 alle 12:00 UTC (17 h DOPO l'evento). Era un ingresso nella reazione al
   FOMC, non prima. Con il calendario ufficiale (federalreserve.gov) solo 2 trade v2 su 105 hanno un FOMC nelle 48 h dopo l'ingresso
   (2023-10-31 e 2024-11-06, entrambi TP); 8 entro +-48 h (2 stop). Il calendario FOMC non spiega gli stop di v2.
8. **Le due tranche dei trade a DCA completa** (49 trade: 27 TP, 22 stop), in R per unita' di rischio della tranche:
   1a tranche: TP +0,46, stop -1,43 (media -0,39); 2a tranche: TP +1,17, stop -0,74 (media +0,31). La 2a tranche da sola ha
   aspettativa positiva: la perdita dei 22 stop nasce soprattutto dalla 1a tranche che si trova 0,71R sotto quando il limit si
   riempie. Ridurre la 2a tranche migliora il rendimento a parita' di coda (r_boot) perche' sposta rischio sui 56 trade a un livello
   (tutti TP, +0,89R), non perche' la 2a tranche sia cattiva. Nota: la condizione "1a in perdita oltre 0,5R" e' sempre vera al
   riempimento del 2° livello (limit a -0,5 ATR = -0,71R).
9. **Short ipervenduti (RSI 4h < 30 o %B 4h < 0 alla conferma)**: 7 short su 26, 3 stop (43%) contro 2 su 19 (10,5%) per gli altri
   short; R medio 0,00 contro +0,31. Il pattern 5 del registro e' confermato nei numeri, ma con n = 7 il placebo (shuffle dei
   x0,6 tra gli short) da' p = 0,15: indizio, non regola. Gli stessi 7 includono tre TP grandi (2022-08-19, 2026-01-29, 2026-06-02).
10. **A parita' di coda la perdita massima per trade non scende con nessuna regola di peso** (v2 -6,8%, R1b60 -7,0%, R3 -7,4% al
   rispettivo r_boot): le riduzioni a base fissa 4,67% vengono solo dalla minore esposizione. L'unica leva sulla perdita massima resta
   il tetto al rischio (L1).
