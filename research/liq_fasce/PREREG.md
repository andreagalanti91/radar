# Preregistrazione · fasce di liquidazione + S/R per ingressi (W3 e intraday) · 13/11/2026, scritta PRIMA dei risultati

Costruisce su: research/liquidazioni (lezione 81: niente calamita, confluenza inutile al tocco giornaliero), studio 03/11
(lezione 72: niente rimbalzo dopo cascate long, d2 su carta), lezioni 68, 75–77 (S/R da soli), 82 (intraday), 90.
Qui la domanda è diversa: la fascia come PREZZO D'ESECUZIONE (limit) per W3 e come BERSAGLIO/PAVIMENTO dopo una cascata oraria.

## Dati e strumenti (congelati)
- Candele 1h Binance USDT-M perp (archivio data.binance.vision) 2021-01 → 2026-11-11; ore dal 12/11 con candele spot Binance
  (data-api). OI = sum_open_interest_value, ultimo valore a 5 minuti DENTRO l'ora (noto alla chiusura dell'ora, lezione 72);
  per le ore di oggi l'OI si prolunga con le variazioni OKX (`liqmap.extend_oi`, come la dashboard).
- Mappa = `radar/liqmap.build` sulle 504 ore precedenti la decisione, `window` ±12%, `clusters(rng 0,10, sig 0,30)`.
  "Fascia densa" = cluster con sig = vero. Mai dati successivi alla decisione.
- S/R = `radar/levels.compute` sulle feature giornaliere fino al giorno PRIMA; confluenza = `liqmap.confluence` (zona ±0,5%)
  con un supporto (fasce long sotto) o una resistenza (fasce short sopra).
- Costi: 0,08% per lato sugli ordini limite e sui trade intraday (perp) + funding reale (giornaliero ripartito sulle ore);
  gli ordini a mercato di W3 restano con i costi del motore (0,1% + slippage 0,1%). Riempimento di un limit solo se il prezzo
  passa oltre il livello di almeno lo 0,05%; prezzo = min(apertura dell'ora, livello) per i buy (simmetrico per i sell).
- Periodi: IS 2021–2023, OOS 2024 → oggi. Riferimenti: W3 com'è (`radar/weekly.simulate`, 10k → 78.474, DD −21,1%) e buy & hold.

## Regole (6 in totale)
**Domanda 2 · W3** (9 long dal 2021: potenza molto bassa, dichiarato prima)
- R1 limit in fascia: al lunedì 00:00 del long W3, limit sulla prima fascia densa di long sotto il prezzo (≤ 10%, sopra lo stop
  iniziale), valido N = 3 giorni; se non si riempie, a mercato all'apertura dopo la scadenza; nessuna fascia → a mercato come W3.
  Stessa esposizione, stop iniziale e uscite di W3. Vicini: N 1 e 7 giorni; sig 0,20 e 0,50.
- R2 limit in confluenza: come R1 ma solo sulla prima fascia densa dentro un supporto; nessuna → a mercato al lunedì.
- R3 presa parziale: dentro un long W3, ogni giorno alle 00:00 limit di vendita di METÀ sulla prima fascia densa di short sopra
  (≤ 10%); dopo il riempimento il resto segue W3. Confronto con d2 dello studio 03/11 (numeri citati, non rifatti).
- Placebo D2: (a) tutti i giorni 2021–2026: vantaggio d'ingresso (prezzo a mercato / prezzo eseguito − 1, costi inclusi, a
  parità di data d'uscita) del limit in fascia contro lo stesso limit a una distanza presa da un altro giorno a caso (1.000
  rimescolamenti); (b) sui long W3: 1.000 estrazioni di distanze casuali dalla stessa distribuzione → percentile del capitale.
- Criterio D2 (tutti): capitale e MAR sopra W3 sia nel 2021–23 sia dal 2024; ≥ 3/4 vicini sopra W3; senza il trade migliore
  ancora sopra; placebo (a) e (b) ≥ 95° percentile. Altrimenti NON ADOTTARE.

**Domanda 3 · intraday dopo cascata**
- Cascata (proxy validato 03/11, ρ 0,61): ora con ΔlogOI ≤ −3σ (σ mobile 30 giorni), volume ≥ 1,5× la mediana 30 giorni,
  rendimento < 0 (cascata LONG) o > 0 (cascata SHORT); eventi a meno di 24 h accorpati. Vicini: k 2 e 4. Controllo con le
  liquidazioni reali Binance coin-margined 2023-06-25 → 2024-10-14: ora con liquidazioni ≥ 99,5° percentile e lato ≥ 75%.
- R4 continuazione: alla chiusura dell'ora di cascata, mappa fino a quell'ora; trade nella direzione della cascata
  (perp, apertura dell'ora dopo) con obiettivo la prossima fascia densa (≤ 10%) e uscita all'orizzonte H se non toccata.
- R5 rimbalzo: il minimo (massimo) dell'ora di cascata entra in una fascia densa della mappa PRE-cascata (fino all'ora prima)
  in confluenza con un supporto (resistenza); esaurimento = l'ora dopo chiude sopra (sotto) la sua apertura senza nuovo
  minimo (massimo); trade contrario alla cascata all'apertura dell'ora successiva, uscita a H.
- Orizzonti H 4, 12, 24, 48 ore; principale H = 24.
- Controlli: (i) ore a caso con lo stesso lato e la stessa regola (1.000 estrazioni); (ii) R4: tasso di tocco della fascia
  contro il tasso di tocco della STESSA distanza da ore qualsiasi (calamita intraday); R5: stesse cascate esaurite senza
  confluenza e con livelli casuali alla stessa distribuzione di distanze.
- Criterio D3 (per regola, H = 24): rendimento netto medio > 0 in IS e in OOS; sopra il controllo (i) con p < 0,05; ≥ 3 dei
  4 orizzonti con lo stesso segno; vicini k 2/4 con lo stesso segno; ≥ 20 eventi per metà (sotto: "insufficiente").
  In conto: 10k a 1x, trade non sovrapposti, capitale finale, DD giornaliero, WR, MAR contro buy & hold e W3.

**Domande 1 e 4**: solo descrittive (cascata del 13/11, livelli reali Hyperliquid/Lighter di data/liqsnap, eventi reali
di data/liq_events). Nessuna regola nasce da questi numeri.

Deviazioni dopo i risultati: scritte in fondo, datate, prima di guardare gli esiti delle varianti nuove.
