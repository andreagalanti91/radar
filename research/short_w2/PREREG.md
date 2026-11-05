# Short W2 · preregistrazione (05/11/2026, scritta PRIMA dei risultati delle regole)

Ipotesi: una strategia SHORT dedicata su BTC (settimanale, perp) guadagna nei bear/crolli più degli short attuali di W2
(4 trade dal 2021, tutti piccoli) e, sostituendo gli short di W2, migliora W2 (rendimento e/o DD) senza toccare i long.

Comune a tutte le regole (stessi parametri ovunque):
- candele W-SUN chiuse; decisione alla chiusura della domenica, esecuzione all'apertura del lunedì (S6: chiusura giornaliera →
  apertura del giorno dopo); slippage 0,1%; commissione 0,1%/lato; funding reale da data/funding.csv (lo short lo incassa se
  positivo), 0 prima del 2020; SMA40w, EMA20w (pendenza 1 sett.), EMA21w, ATR14w, MACD(8,21,5) come in radar/weekly.py.
- stop iniziale 2,5 ATRw dalla chiusura del segnale, trailing 2,5 ATRw dalla miglior chiusura giornaliera (controllo giornaliero);
  liquidazione se il prezzo sale di 1/esposizione (+100% a 1x).
- size: 1x (100% dell'equity) e R25 = min(1, 0,25 / (2,5·ATRw/close)) come W2.
- regime ribassista base: chiusura < SMA40w ed EMA20w in calo.

Regole (≤ 8):
- S0 = short attuale W2 (riferimento): regime W2 (anche SMA40 in calo su 4 sett.) + chiusura < EMA21 + pf14z < 0;
  uscite EMA21, distribuzione short (funding7 < −0,0003 e pf14z > 0), trailing.
- S1 regime: regime base + chiusura < EMA21w; uscita chiusura > EMA21w, trailing.
- S2 = S1 + MACD < segnale e MACD < 0 (specchio di F1).
- S3 = S2 + flusso perp pf14z < 0 + longs affollati (funding_z > 0 oppure ls_z > 0, ls solo dal 12/2021).
- S4 ritest fallito: SMA40 in calo su 4 sett., massimo settimanale ≥ min(EMA21, SMA40) − 0,25 ATRw, chiusura < EMA21
  e candela rossa; uscite come S1.
- S5 top di distribuzione: incrocio MACD al ribasso sopra lo zero + chiusura > 1,25·SMA40 + funding_z > 1 (longs affollati);
  stop stretto 1,5 ATRw, trailing 2,5 ATRw, uscita su incrocio MACD al rialzo o dopo 8 settimane.
- S6 = S2 con timing giornaliero: armata dalle condizioni S2 dell'ultima settimana chiusa; ingresso alla prima chiusura
  giornaliera sotto il minimo dei 7 giorni precedenti e sotto la EMA21w; uscite come S1.
- S7 = S2 con uscita lenta: niente uscita su EMA21, uscita su chiusura settimanale > SMA40w o trailing.

Metriche dal 01/01/2021 (10.000 $), standalone e combinate con i long W2 (gli short W2 sostituiti).
Robustezza: 2021–23 vs 2024–oggi; 2018–20 con dati Bitstamp/Binance spot (flusso = CVD spot z come proxy, niente funding);
parametri vicini (SMA 35/45, EMA uscita 18/24, trailing 2/3, MACD 6/18/4 e 10/26/6); senza il trade migliore; placebo
(stessi numeri di trade a ingressi casuali nelle settimane di regime base, 500 prove).
Promozione solo se: combinato batte W2 in MAR in ENTRAMBI i sottoperiodi e nel 2018–20, la famiglia dei vicini lo conferma
(mediana), regge senza il trade migliore e il placebo è sotto il 10% (p < 0,10).
