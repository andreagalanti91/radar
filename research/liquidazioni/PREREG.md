# Preregistrazione · "calamita" delle liquidazioni stimate e confluenza con S/R (07/11/2026, scritta PRIMA dei risultati)

Dati: Binance USDT-M BTCUSDT, OI a 5 minuti (archivio metrics, ultimo valore dentro l'ora = OI alla chiusura, nessun dato dal
futuro) e candele perp 1h, 2021-01-01 → 2026-11-02. Mappa = `radar/liqmap.build` (stessa funzione della dashboard): 21 giorni di
OI orario, leve 10/25/50/100x (30/30/25/15%), MM 0,5%, metà long metà short. Una mappa al giorno, alla chiusura delle 00:00 UTC.
Cluster = `radar/liqmap.clusters` (picchi su 3 fasce dello 0,25%, "significativo" ≥ 30% del più grande del lato entro ±10%).
Split: P1 2021-01 → 2023-12, P2 2024-01 → 2026-11.

T1 · calamita (6 test: lato sopra/sotto × orizzonte 1/3/7 giorni). Evento = cluster significativo più vicino per lato, distanza d.
Esito = il prezzo tocca il livello entro H (massimo ≥ livello sopra, minimo ≤ livello sotto, candele orarie dopo la mappa).
Controllo a pari distanza: probabilità di toccare un livello alla STESSA distanza d sullo stesso lato partendo da un giorno
qualsiasi del campione (stima empirica sui ~2.100 giorni, escluso il giorno stesso). Effetto = tasso − controllo.
T2 · direzione (3 test: H = 1/3/7 giorni). Ogni giorno con un cluster significativo per lato: quale si tocca per primo entro H.
Atteso senza informazione (moto senza deriva): P(sopra prima) = d_sotto / (d_sopra + d_sotto). Si confronta l'esito reale con
l'atteso nei giorni in cui il lato più "pesante" (squilibrio entro ±5% ≥ 20% in valore assoluto) è sopra o sotto:
effetto = (tocchi del lato pesante − atteso) in punti percentuali.
T3 · confluenza (2 test): primo tocco di un cluster significativo entro 7 giorni; rimbalzo = nessuna chiusura giornaliera oltre il
livello di oltre lo 0,5% nei 3 giorni dopo il tocco, altrimenti rottura. Tasso di rimbalzo dei cluster dentro una zona S/R
(`radar/levels.compute` calcolato con i dati fino al giorno della mappa, zona allargata dello 0,5%) contro i cluster fuori;
e S/R da soli (tocco della zona S/R più vicina per lato) contro cluster confluenti.
Placebo T3: 1.000 permutazioni dell'etichetta "confluente" fra i tocchi.

Criterio (per OGNI test): effetto ≥ 5 punti, p < 0,05 (binomiale per T1/T2, permutazione per T3) e stesso segno in P1 e P2.
Giudizio per famiglia: l'idea "funziona" solo se passa ≥ 2/3 dei test della famiglia. Effetti sotto 5 punti = nessun vantaggio
pratico. Se nulla passa: la mappa resta contesto visivo, non entra in W2 + MACD.
