# trend_multi · portafoglio di trend-following su molti mercati — PREREGISTRAZIONE (23/11/2026)

Scritto e committato da solo PRIMA di scaricare i dati e di calcolare qualsiasi rendimento. Nessun parametro è stato provato:
tutto ciò che segue è fissato a priori dalla letteratura (Moskowitz-Ooi-Pedersen 2012; Hurst-Ooi-Pedersen 2017; Faber 2007).
Novità rispetto alle lezioni 104, 107, 110, 117: non una regola giudicata mercato per mercato, ma un PORTAFOGLIO di molti
mercati poco correlati, con posizioni a rischio uguale, giudicato solo come portafoglio. BTC ed ETH esclusi (li copre W3.2).

## Universo (fissato ora; date di avvio attese a memoria, da confermare sui dati e riportare nel README)
19 ETF USA in USD, classi ampie (non singoli vincitori). Fonte: Yahoo chart API pubblica (stessa funzione di
research/multi_asset/fetch.py), chiusure giornaliere rettificate per split e dividendi, taglio 20/11/2026.
- Azioni (7): SPY (1993), QQQ (1999), IWM (2000), EFA (2001), VGK (2005), EEM (2003), EWJ (1996)
- Obbligazioni (4): IEF (2002), TLT (2002), LQD (2002), HYG (2007)
- Materie prime (4): GLD (2004), SLV (2006), DBC (2006), USO (2006)
- Valute (3): UUP (2007), FXE (2005), FXY (2007) — UUP e FXE sono quasi speculari: dichiarato, non corretto
- Immobiliare (1): VNQ (2004)
SHY non è un mercato dell'universo (volatilità troppo bassa: dominerebbe i pesi): serve solo come variante della liquidità.
Liquidità: tasso T-bill a 13 settimane (^IRX di Yahoo, rendimento/252 al giorno); se non scaricabile, SHY. Un ETF che la fonte
non restituisce esce dall'universo e si dichiara. Bias dichiarato: elenco scelto oggi (ETF sopravvissuti e liquidi).
Un mercato entra quando ha 273 sedute di storia. Simulazione dal 31/01/2007 con i mercati disponibili.

## Regole
- **Segnale** (primario, Hurst-Ooi-Pedersen): per ogni mercato, rendimento totale meno rendimento della liquidità su 21, 63 e
  252 sedute; long/flat: s = quota dei tre orizzonti con eccesso > 0 (0, 1/3, 2/3, 1); long/short: s = media dei segni (−1…+1).
- **Dimensione**: σ_i = dev. standard degli ultimi 60 rendimenti giornalieri × √252 (minimo 1%); u_i = s_i/σ_i (rischio uguale
  per mercato); k = 10% / volatilità stimata del portafoglio u (covarianza a 60 sedute); w = k·u; se Σ|w| > L si riduce tutto in
  proporzione. **Primaria L = 1 (nessuna leva)**; L = 2 solo descrittiva.
- **Ribilanciamento**: mensile; segnali e pesi alla chiusura dell'ultima seduta del mese, eseguiti alla chiusura della seduta
  successiva; fra un ribilanciamento e l'altro le posizioni derivano con i prezzi (nessun ritocco).
- **Costi**: 0,10% del controvalore scambiato per lato (0,05% commissione + 0,05% slippage); short: 1% annuo sul nozionale corto.
  Liquidità remunerata solo su 1 − Σ|w| (i proventi degli short non rendono: prudente).
- Solo numpy/pandas. Stessi parametri per tutti i mercati.

## Varianti (8 in tutto; candidate al giudizio solo V1 e V2)
| | Lato | Segnale | Ribil. | L | Ruolo |
|---|---|---|---|---|---|
| V1 | long/flat | 1/3/12 mesi | mensile | 1 | **primaria** |
| V2 | long/short | 1/3/12 mesi | mensile | 1 | candidata |
| V3 | long/flat | 3/6/12 mesi (63/126/252) | mensile | 1 | robustezza |
| V4 | long/flat | 12 mesi (252) | mensile | 1 | robustezza |
| V5 | long/flat | prezzo > media a 10 mesi (210 sedute) | mensile | 1 | robustezza |
| V6 | long/flat | 1/3/12 mesi | settimanale (ultima seduta della settimana) | 1 | robustezza |
| V7 | long/flat | 1/3/12 mesi | mensile | 2 | descrittiva (leva) |
| V8 | long/short | 3/6/12 mesi | mensile | 1 | robustezza |
Controlli su V1 e V2 (non varianti della regola, non selezionabili): costi doppi (0,20% per lato, short 2%); liquidità a zero e
liquidità = SHY; finestra di volatilità 40 e 90 sedute; senza ciascuna delle 5 classi a turno; banda pratica (non si scambia
se |Δw| < 1% del capitale). Nessuna variante o controllo può sostituire V1/V2 nel verdetto.

## Riferimenti (stessi costi, ribilanciamento mensile)
60/40 SPY/IEF; equipesato dei mercati disponibili dell'universo; tutto in liquidità (T-bill).

## Periodi
- Sviluppo (solo descrittivo, nessuna scelta da fare perché tutto è fissato): 31/01/2007 → 31/12/2015 (include il 2008,
  favorevole al trend: dichiarato).
- **GIUDIZIO: 01/01/2016 → 20/11/2026, calcolato una sola volta.** Metà: 2016–2020 e 2021–2026.
- Crisi: 2018 Q4 (01/10–31/12/2018); 19/02–23/03/2020 e mese di marzo 2020; anno 2022.

## Metriche
CAGR, volatilità annua, max drawdown giornaliero, CAGR/DD, Sharpe (su eccesso rispetto al T-bill), peggior anno solare; cambi
di stato del segnale per anno (un mercato entra, esce o si inverte) e ordini per anno con |Δw| ≥ 1% del capitale; rotazione
annua; esposizione lorda media e quota di giorni investiti (lordo > 5%).

## Criteri di validità (periodo di giudizio; tutti necessari; applicati a V1 e a V2 separatamente)
1. CAGR/DD > 60/40 e > equipesato;
2. max DD ≥ −25%;
3. rendimento positivo in entrambe le metà (2016–20 e 2021–26) e CAGR > CAGR della liquidità;
4. rendimento giornaliero in eccesso sul T-bill > 0 con bootstrap a blocchi circolari (blocchi di 63 sedute, 10.000
   ricampionamenti, seme 118, una coda, ipotesi nulla centrata): p < 0,025 (Bonferroni per 2 candidate).
**Verdetto**: "funziona" = 1–4 tutti veri per almeno una candidata e robusto (sotto); "non funziona" = fallisce 1, 2 o 3;
"non dimostrabile" = passa 1–3 ma non 4, oppure passa 1–4 ma non la robustezza.
**"Vale la pena rispetto al 60/40"**: in più, differenza di Sharpe contro il 60/40 > 0 con bootstrap appaiato (stessi blocchi),
p < 0,05; altrimenti "non distinguibile dal 60/40". Stessa prova, descrittiva, contro l'equipesato.
**Robustezza** (su ogni candidata che passa 1–4): CAGR/DD > 60/40 in almeno 4 su 5 esclusioni di classe, in almeno 2 su 3 dei
segnali alternativi (V3–V5 per V1; V8 per V2 più gli stessi controlli), con ribilanciamento settimanale e con costi doppi.

## Combinazione con W3.2 (solo descrittiva)
W3.2 BTC (`radar.weekly.simulate` sui dati del repo, atteso 78.474 $) ha già visto tutto il 2021–26: nessun criterio.
Dal 01/01/2021: correlazione dei rendimenti mensili fra V1 (e V2) e W3.2; portafogli misti W3.2/trend 70/30, 50/50 e 30/70
ribilanciati a fine mese: finale, CAGR, DD, CAGR/DD contro W3.2 da sola.

## Pratica (README)
Posizioni che V1 terrebbe oggi; con 60.000 $: dollari per posizione, ordini al mese; nota PRIIPs (ETF USA non acquistabili dai
clienti al dettaglio UE: servono equivalenti UCITS o future/CFD; nessun ticker indicato senza certezza).
