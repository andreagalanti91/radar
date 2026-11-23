# Preregistrazione · forza giornaliera: chi compra (spot contro perp), livelli chiave, uso su W3.2 · 23/11/2026

Scritta PRIMA di qualsiasi rendimento. Finora è stato eseguito solo `fg_count.py` (numerosità degli eventi, nessun rendimento:
`conteggi.txt`). Va committata da sola. Regole, soglie e varianti non si cambiano dopo; ogni idea nata dai risultati va in una
nuova preregistrazione. Una variante che passa NON entra in radar/: si segnala.

## 1. Domanda
W3.2 (settimanale) decide la direzione. L'utente vuole controllare ogni giorno la "forza" (chi compra: spot o perp; livelli
chiave; liquidazioni) per entrare o uscire meglio. Spunto: messaggio di un trader del 23/11 ("when spot leads, a move has legs;
when perps carry it alone it ends fast"; rimbalzo 55,1k → 61k con perp +880 M$ contro spot +23 M$, livello 62,5k).
Già nel diario, non ripetuto: caso opposto perp vende/spot assorbe (flusso_trader, 11/11: solo contesto); ingressi DCA, a limite
e 7 giorni (lezione 105); livelli settimanali come segnale (75–77, 106); fasce e squilibri di liquidazione come ingressi (92,
93); sentiment da liquidazioni (108); TP fissi (109). Novità: classificare OGNI movimento giornaliero per chi lo guida e usarlo
(a) come previsione a 3–14 giorni, (b) come conferma delle rotture, (c) come ritardo d'ingresso e uscita anticipata su W3.2.

## 2. Dati
- BTC: `research/p2_nuovi/data/f_repo.csv.gz` (Binance BTCUSDT spot e perp USDT-M giornaliero, congelato al 15/11/2026).
  spot_delta e perp_delta = taker buy − taker sell (BTC). Perp dal 2020-01, z a 180 giorni validi da metà 2020.
- Campione eventi: 01/01/2021 → 15/11/2026; metà 2021–23 / 2024→. ETH (`radar.data.load_asset("ETH")` + build_features, tagliato
  al 15/11): stessi parametri, sola conferma esterna, fuori dal conteggio di Holm.
- 2018–20: frame lungo `f_long` (W3.2 = 25.142 $). I flussi spot/perp esistono solo dal 2020 (z validi da metà 2020): prima la
  regola è INATTIVA (variante = W3.2). Il criterio 2018–20 è quindi quasi vuoto: lo dichiaro.
- Solo Binance: i numeri del trader (probabilmente aggregati su più borse) non sono confrontabili in valore assoluto.
- Liquidazioni: NON testate qui. Dati reali disponibili solo Binance COIN-M 06/2023 → 10/2024 (472 giorni, ~3 trade W3.2) e
  registro eventi dal 10/11/2026 (< 10% del mercato); le mappe stimate sono già state provate come ingressi (lezioni 92, 93) e
  come segnale orario (108). Nessun test dal 2021 è possibile con liquidazioni reali.

## 3. Definizioni (fissate dopo i soli conteggi)
- Flussi a N giorni: pfN = Σ perp_delta / Σ perp_vol, sfN idem spot; pzN, szN = z su 180 giorni (radar.features._z).
- Movimento: upN = chiusura / minimo degli ultimi N giorni (oggi compreso) − 1; dnN = chiusura / massimo degli ultimi N giorni − 1.
- Evento rialzo: primo giorno con upN ≥ X, poi pausa 7 giorni. Evento ribasso: dnN ≤ −X. **Primario N = 3, X = 5%.**
- Chi guida (verso = +1 acquisti, −1 vendite), **D0 = 0,5**:
  "perp" = pz·verso > 0 e (pz − sz)·verso ≥ D0; "spot" = sz·verso > 0 e (sz − pz)·verso ≥ D0; "misto" = il resto.
- Livello chiave giornaliero: massimo/minimo dei 20 giorni precedenti (rottura = chiusura oltre il livello).
  Livello settimanale: swing di `research/swing_sr/sw_engine.py` (segnale "X", K = 3, 104 settimane).
- Rendimento successivo: chiusura t → chiusura t+h, h = 3, 7, 14 giorni. **Orizzonte primario 7 giorni.**
Conteggi (BTC 2021→, N 3, X 5%, D0 0,5): rialzi 163 (perp 50, spot 37, misto 76); ribassi 141 (perp 51, spot 32, misto 58);
rotture 20 g: su 62 (spot 21, perp 18), giù 45 (spot 14, perp 17); rotture swing settimanale: su 92, giù 90.

## 4. Test evento (5 test primari, a 7 giorni, bilaterali)
| Id | Ipotesi | Confronto | Segno atteso |
|---|---|---|---|
| T1 | H1 squeeze a leva | rialzi "perp" − rialzi "spot" | < 0 |
| T2 | H1 speculare (flush a leva) | ribassi "perp" − ribassi "spot" | > 0 |
| T3 | H2 spot che guida | rialzi "spot" − media di tutti i giorni | > 0 |
| T4 | H3 livello 20 g + spot | rotture (su e giù insieme, rendimento nel verso della rottura) "spot" − "perp" | > 0 |
| T5 | H3 livello swing settimanale + spot | come T4 sui segnali "X" | > 0 |
- p di T1, T2, T4, T5: permutazione delle etichette di classe fra gli eventi dello stesso anno (5.000, seme 20261123).
- p di T3 (e descrittivo per ogni classe contro la media): spostamento circolare a blocchi della serie degli eventi (5.000,
  spostamento ≥ 30 giorni).
- Riportati anche: h = 3 e 14, due metà, classe "misto", ogni classe contro la media incondizionata, ETH.
- Vicini (descrittivi, 5): (N 2, X 5%), (N 5, X 5%), (N 3, X 4%), (N 3, X 6%), D0 = 1,0; più la versione "in dollari" del trader
  (perp = netto perp nel verso e spot contrario oppure rapporto ≥ 2 × rapporto mediano dei volumi a 180 giorni).
- Esito "utile": segno atteso, |effetto| ≥ 1 punto a 7 g, p ≤ soglia di Holm (13 test, α 0,05), stesso segno nelle due metà,
  ≥ 4 vicini su 5 con lo stesso segno, ≥ 15 eventi per classe. "Solo contesto": segno atteso in entrambe le metà e p nominale
  < 0,10. Altrimenti "nessun effetto".

## 5. Uso su W3.2 (8 varianti; motore `fg_engine.py`, copia di radar.weekly.simulate come tp_engine/iu_engine)
Riferimento W3.2: 78.474 $, DD −21,1%, 13 trade (IS 33.477 $, OOS 23.488 $, 2018–20 25.142 $). Stessi costi, stessa esposizione
(calcolata sulla settimana del segnale), stesso stop iniziale e trailing. Segnali valutati alla chiusura, eseguiti all'apertura
successiva. Giorno 0 = domenica della decisione; W3.2 entra all'apertura del giorno 1.

Ingressi (E-in):
| Id | Regola |
|---|---|
| E-in1 | ingresso all'apertura dopo il primo giorno, fra 0 e 2, con pz1·lato > 0 e sz1·lato > 0; se nessuno, apertura del giorno 4 (K = 3) |
| E-in2 | come E-in1 con K = 5 (giorni 0–4, altrimenti apertura del giorno 6) |
| E-in3 | come E-in2 con flussi a 3 giorni (pz3, sz3) |
| E-in4 | limite sul livello di swing settimanale più vicino dal lato favorevole (sotto per i long, sopra per gli short) entro il 6% dalla chiusura del segnale, valido nei giorni 1–5; non eseguito → mercato all'apertura del giorno 6; nessun livello entro il 6% → come W3.2 |
Uscite anticipate (E-out), con posizione aperta, alla chiusura giornaliera:
rottura contraria = chiusura sotto il minimo (long) / sopra il massimo (short) degli L giorni precedenti; "guidata dallo spot" =
classe "spot" del movimento contrario a 3 giorni (D0 0,5); "con spot" = sz3 nel verso contrario. Mai uscita se la classe è "perp".
Uscita all'apertura successiva; rientro all'apertura del lunedì dopo la prima decisione domenicale successiva all'uscita in cui
il trade W3.2 è ancora aperto (stop/trailing non toccato, nessuna uscita EMA/distribuzione), alla stessa esposizione sul capitale
corrente; stop e trailing del trade continuano come in W3.2. Se W3.2 esce mentre si è fuori, il trade finisce lì. La regola può
scattare più volte nello stesso trade.
| Id | Regola |
|---|---|
| E-out1 | uscita totale, L = 20, guidata dallo spot |
| E-out2 | uscita di metà, L = 20, guidata dallo spot |
| E-out3 | uscita totale, L = 10, guidata dallo spot |
| E-out4 | uscita totale, L = 20, "con spot" |
Controllo (non è una variante): uscita su ogni rottura a 20 giorni senza guardare il flusso, per isolare il contributo del flusso.
Zone di liquidazione come ingresso: non ripetute (lezioni 92, 93; nessun dato reale dal 2021).

Metriche: finale, CAGR, max DD giornaliero, CAGR/DD, trade, WR, peggiore; 2021+, IS 2021–23, OOS 2024–26 (ripartono da 10.000 $),
2018–20; buy & hold. Un trade = un segnale W3.2 (uscite e rientri dentro lo stesso trade).
Criteri (tutti): C1 CAGR/DD > W3.2 sia IS sia OOS · C2 2018–20 CAGR/DD non peggiore · C3 DD 2021+ entro −30% · C4 WR ≥ 70% ·
C5 Σ Δ log-rendimento per trade (variante − W3.2) > 0 anche tolti i 2 Δ più favorevoli · C6 permutazione dei segni sui Δ per
trade, p ≤ soglia di Holm (13 test) · C7 placebo p < 0,05: E-in = ritardo estratto a caso fra 0 e K giorni per trade (E-in4:
stessa quota di trade ritardati, ritardo casuale 0–5); E-out = stesso numero di uscite anticipate in giorni casuali degli stessi
trade (500 ripetizioni, p = quota con CAGR/DD 2021+ ≥ variante).
ETH: stesse 8 varianti, stesse metriche; conferma esterna (stesso segno del Δ CAGR/DD), non criterio e non ottimizzazione.
Potenza: 13 trade. Il p minimo della permutazione dei segni con m Δ non nulli è 2^−m: con Holm su 13 test (0,0038) servono
almeno 9 trade modificati tutti a favore. Mi aspetto "non dimostrabile" come esito più probabile anche per una regola buona.

## 6. E-hold (descrittivo, nessun criterio)
Per ogni trade W3.2 (BTC ed ETH): movimenti contrari ≥ 5% in 3 giorni (primo giorno, pausa 7) per classe (perp / spot / misto);
per ciascuno: rendimento nel verso del trade a 7 giorni e fino all'uscita, se la miglior chiusura precedente è stata superata,
motivo dell'uscita. Conteggi BTC: perp 35, spot 14, misto 24.

## 7. Caso 21–23/11 e stato di oggi (descrittivo)
Delta spot e perp giornalieri e orari (Binance; il 23/11 perp solo da OKX, provvisorio) dal minimo del 21/11; confronto con i
numeri del trader; classe che le regole del punto 3 assegnano al rimbalzo per BTC ed ETH; stato rispetto al massimo a 20 giorni.
