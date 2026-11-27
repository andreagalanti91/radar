# Deviazioni e precisazioni rispetto al PREREG (commit 14cadc0)

Nessuna definizione, soglia o periodo è stato cambiato dopo i risultati. Le voci sotto sono interpretazioni di punti che il
PREREG non fissava del tutto, o limiti di realizzazione, dichiarati qui.

1. **Criterio (c), "almeno 3 vicini su 4"**: il PREREG elenca 1–3 vicini per variante (V1–V2: 3; V3–V5, V7: 2; V6: 1). Il
   criterio si applica come "almeno il 75% dei vicini elencati con lo stesso segno in OOS". Nessun verdetto dipende da questa
   lettura: le varianti che falliscono (c) falliscono anche (a).
2. **V3 e V4 danno la stessa regola operativa.** Stesso indicatore, stesso segno IS (−), stessi terzili e ritenzione di 7 giorni
   per costruzione del PREREG: le righe di `regole.csv` coincidono.
3. **Risoluzione del placebo a slittamento circolare**: con n domeniche OOS gli slittamenti distinti sono n − 15 (circa 125–135
   per V1–V6; 19 per il placebo della regola V7 su 34 scadenze). Le 10.000 estrazioni (seme 20261127) ricampionano questi valori:
   il p minimo vero è circa 1/130 (1/19 per la regola V7), anche quando il file riporta 0,0001.
4. **p IS**: è calcolato nel verso stimato sulla stessa IS, quindi è ottimista per costruzione. Serve solo come informazione,
   non entra in nessun criterio.
5. **Short in perp a 1x**: esposizione ribilanciata ogni giorno (rendimento giornaliero = −r + funding del giorno). È
   un'approssimazione dello short a nozionale fisso, con differenze piccole su posizioni da 7 giorni.
6. **Regola V7**: la valutazione giornaliera usa le aperture orarie delle 00:00 (`opzioni_studio/cache/btc_1h.csv`). Il funding
   degli short è sommato giorno per giorno, con un terzo del giorno di scadenza (08:00).
7. **V8**: i segnali di W3.2 prima del 28/03/2021 non hanno DVOL, quindi non sono filtrati: dal 2021 è il solo segnale
   2021-01-31. In OOS nessun segnale supera la soglia q75 (1,43): il filtro coincide con B0r e il p appaiato vale 1.
8. **W3.2 "com'è"**: `radar.weekly.simulate` sul frame di `opzioni_studio` (`op_segnali.frame()`). IS e OOS sono simulati da
   soli, partendo flat da 10.000 $; dal 2021 è continuo. Le operazioni comprendono quella aperta al 21/11, valutata alla
   chiusura con la commissione. Il buy & hold va dall'apertura del primo giorno alla chiusura dell'ultimo. Le regole R partono
   dal lunedì dopo la prima domenica del periodo (il 04/01/2021 per l'IS).
9. **Scadenza del 27/11/2026**: osservazione solo descrittiva, fuori dal test, come chiesto. Fonti: istantanea Deribit delle
   07:38 (`research/opzioni_scadenze/dati/snap_20261127_0738.json`) e `get_delivery_prices` (btc_usd).

10. **Dalla revisione critica**: V2 = −V1 (posizioni speculari nel 100% delle settimane, stessa tenuta di 7 g), come V3 = V4. p di V6 ricalcolato esatto su tutti gli slittamenti: 0,0074 OOS (Holm ≈ 0,06); il valore 0,0001 era la risoluzione del ricampionamento.
