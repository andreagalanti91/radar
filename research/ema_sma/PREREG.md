# Preregistrazione · EMA e SMA su BTC a 4 ore, giornaliero e settimanale: atlante dei pattern e regole long/short · 23/11/2026

Scritta PRIMA di qualsiasi rendimento (di strategia o dopo un evento). Finora eseguiti solo: `fetch.py` (scarico delle candele 4h),
il controllo che le candele giornaliere ricostruite dal 4h coincidano con i dati del repo (2017-08-17 → 2026-11-15: apertura,
massimo, minimo e chiusura identici su 3.378 giorni, scarto massimo 0) e `es_lib.py` (conta le regole della grammatica: 4.017).
Va committata da sola. Definizioni, soglie, criteri e modo di scegliere non si cambiano dopo; ogni idea nata dai risultati va in
una nuova preregistrazione. Ordine di esecuzione: Parte B scoperta → scelta → giudizio e conferma → Parte A (l'atlante usa
anche il 2024–26 e quindi si guarda solo dopo che la scelta è scritta su file).

## 1. Domanda dell'utente e cosa è già noto
"Studio con EMA e SMA dal 2021: chiusure giornaliere, settimanali, 4h. Trova pattern ricorrenti; entrata e uscita, long/short.
Esempio: quando chiude sopra la SMA200 giornaliera long → quando il 4h chiude due volte di seguito sotto una media chiudo e apro
short. Voglio una coerenza di analisi tecnica."
Già noto (non si ripete come scoperta): trend long/flat su SMA 50/100/200 giornaliere = unico vantaggio stabile ma WR 24%, DD −33%,
scegliere il "miglior" trend è rumore (Giro 9); 200 giorni ≈ MACD > 0, nessuna regola tecnica robusta (79, 83); schema
multi-intervallo e 15 indicatori: negativo (censimento); rotture 4h a mano: nessun vantaggio dopo i costi (78, 82); short dedicati
sotto gli short di W2 (80). Novità di questo studio: grammatica dichiarata regime × innesco × uscita × lato su tre intervalli,
uscite a 4h con N chiusure consecutive, inversione long/short dell'esempio, scoperta e giudizio separati con correzione per le
prove multiple, atlante descrittivo con placebo.

## 2. Dati, intervalli, medie
- BTCUSDT spot Binance, candele 4h dall'archivio pubblico data.binance.vision (2017-08-17 → 2026-11-22, UTC, 20.292 barre; 9
  buchi di 8–32 ore nel 2017–20, nessuno dal 2021). Giornaliero = 6 barre 4h (00:00–24:00 UTC), coincide con il repo. Settimanale
  W-SUN come W3.2 (solo settimane chiuse). Per scaldare le medie giornaliere e settimanali prima del 2017-08 si usa il giornaliero
  del repo (research/p2_nuovi/data/f_long, dal 2014). Lo studio finisce il 15/11/2026 (dati congelati di W3.2).
- Medie (`es_lib.ma`, unica funzione anche per le tabelle DATI*.md): SMA n = media semplice di n chiusure; EMA n = ewm(span = n,
  adjust = False) dalla prima chiusura, valida dopo n chiusure. Periodi 20, 50, 100, 200 su 4h, 1D, 1W; in più 21 e 40 sul
  settimanale (solo atlante e regime G5).
- Periodi: **scoperta 2021-01-01 → 2023-12-31**; **giudizio 2024-01-01 → 2026-11-15** (mai guardato prima della scelta);
  **conferma 2018-01-01 → 2020-12-31** (mai guardato prima della scelta).

## 3. PARTE B · grammatica (4.017 regole, 87 famiglie)
Tutte le condizioni sono note alla chiusura di una candela 4h; un valore giornaliero/settimanale vale dalla chiusura della candela
4h delle 20:00 UTC (ultima del giorno / della domenica). Il lato short è lo specchio del lato long.
**Regime G (6)**: G0 nessuno; G1 chiusura 1D sopra/sotto SMA200; G2 chiusura 1D sopra/sotto EMA200; G3 SMA50 1D sopra/sotto
SMA200 1D (stato golden/death cross); G4 chiusura 1W sopra/sotto EMA20 1W; G5 chiusura 1W sopra/sotto SMA40 1W.
**Innesco E (3)**: E0 nessuno; E1 chiusura 1D sopra (long) / sotto (short) la EMA20 1D; E2 ritest: negli ultimi 3 giorni chiusi
almeno un minimo ≤ EMA50 1D e ultima chiusura 1D > EMA50 1D (short: massimo ≥ EMA50 e chiusura < EMA50).
**Uscita X (59)**:
- C (48): stato con isteresi F(intervallo, media, N): +1 dopo N chiusure consecutive sopra la media, −1 dopo N consecutive sotto,
  altrimenti invariato; intervallo 4h o 1D × EMA/SMA × 20/50/100/200 × N 1/2/3. Il long esce quando F = −1, lo short quando F = +1.
- X (8): incrocio fra due medie dello stesso tipo, stato sign(veloce − lenta): coppie 20/50 e 50/200 × EMA/SMA × 4h/1D.
- A (3): stop e trailing a k ATR14 giornalieri (Wilder), k = 2, 3, 4: stop iniziale = chiusura del segnale − k·ATR; poi
  max(stop, migliore chiusura 4h − k·ATR corrente), a cricchetto; toccato dentro la barra 4h → uscita a min(apertura, stop).
**Ingresso**: condizione long CL = (regime long) e (innesco long) e (per le uscite C e X: stato d'uscita = +1). Si entra
all'apertura della candela 4h successiva quando CL passa da falsa a vera (fronte di salita) e non si è già long. Il regime e
l'innesco contano solo per entrare: una volta dentro si esce solo con la regola d'uscita. Dopo un'uscita su stop ATR si rientra solo
a un nuovo fronte.
**Lato (4)**: LO solo long; SO solo short; LS long e short (un segnale d'ingresso opposto chiude e inverte); INV = esempio
dell'utente: long come LO; short a ogni passaggio dello stato d'uscita a −1 in qualsiasi regime, senza innesco (chiudo il long e
apro lo short), ricoperto quando lo stato torna +1 (poi long solo se regime e innesco lo consentono).
Esclusi (degeneri o doppioni): INV con uscite A; INV con G0; G0 + E0 con uscite A. Totale 4.017 regole.
**Esempio dell'utente (24 regole dentro la grammatica)**: regime G1 (chiusura 1D sopra la SMA200), innesco E0, uscita C a 4h con
N = 2 su EMA/SMA 20/50/100/200, nei tre lati INV (letterale: inversione short), LS (short solo sotto la SMA200) e LO (senza
short). Regola di riferimento dichiarata ora: **U = INV | G1 | E0 | 4h, EMA50, N = 2**. Si giudica comunque, insieme alla mediana
delle 8 medie del lato INV.

## 4. Esecuzione e costi (motore `es_engine.py`, barra per barra a 4h, tutte le regole insieme)
Decisione alla chiusura della candela 4h, esecuzione all'apertura della successiva. 10.000 $, 1x, tutto il capitale. Long in
spot: commissione 0,1% + slippage 0,1% per lato. Short in perp: 0,05% + slippage 0,1% per lato, funding reale giornaliero
(f_long/f_repo, disponibile dal 2020-01-01; prima = 0: dichiarato, favorisce gli short nel 2018–19) ripartito sulle 6 candele;
prezzo spot anche per lo short (base ignorata). Short a quantità fissa (non ribilanciato). Simulazione continua dal 2018-01-01; i
periodi sono fette della stessa curva (una posizione aperta attraversa il confine); un trade appartiene al periodo d'ingresso.
Metriche per periodo: capitale finale da 10.000 $, CAGR, max drawdown sulle chiusure giornaliere, S = CAGR/|DD|, trade, win rate.
Buy & hold: comprato all'apertura del primo giorno del periodo con gli stessi costi.
Versione "tetto di rischio" (solo per la regola scelta e per U, confronto alla pari con W3.2): esposizione = min(1; 0,25 /
(2,5·ATR settimanale/chiusura)) all'ingresso e stop di protezione a 2,5 ATR settimanali dalla chiusura del segnale.

## 5. Scoperta (solo 2021–23) e modo di scegliere
- Regola valida in scoperta: ≥ 15 trade e DD ≥ −35%. S′ = S se valida, altrimenti min(S, 0).
- Famiglia = lato × regime × classe d'uscita (C-4h, C-1D, X, A): 87 famiglie da 6 a 72 regole. Punteggio della famiglia = mediana
  di S′ dei suoi membri; ammessa se almeno metà dei membri è valida.
- **Scelta**: la famiglia ammessa con il punteggio più alto; al suo interno la regola valida con il punteggio dei vicini più alto
  (mediana di S′ di sé stessa e dei vicini; vicino = stessa famiglia, una sola coordinata diversa: innesco qualsiasi, EMA↔SMA,
  periodo a un passo fra 20/50/100/200, N a un passo; per X: intervallo, tipo, coppia; per A: k a un passo); a parità, S′ più alto.
  Se nessuna famiglia è ammessa: "nessuna regola scelta" e si giudica comunque, come descrizione, la famiglia a punteggio massimo.
  La scelta si scrive in `scelta.json` prima di calcolare giudizio e conferma.
- Quanto è buono il migliore per caso: (a) le 4.017 regole su 200 serie 2021–23 rimescolate a blocchi di 20 giorni (rapporti
  O/H/L/C sulla chiusura precedente, blocchi di 120 candele permutati; storia precedente reale; funding alle date reali): distribuzione
  del massimo di S′ e del massimo punteggio di famiglia; p di selezione = quota di serie in cui il miglior punteggio di famiglia ≥
  quello reale; (b) White reality check con bootstrap stazionario (blocco medio 10 giorni, 2.000 ricampionamenti) sul rendimento
  logaritmico giornaliero medio delle regole valide, contro zero e contro il buy & hold.
- Mappe: punteggio per famiglia, per lato, per regime, per classe e intervallo d'uscita, EMA contro SMA, per periodo e N.

## 6. Giudizio (una sola volta) e conferma · criteri di validità
La regola scelta (e, separatamente, U) è **valida** solo se, sia nel giudizio 2024–26 sia nella conferma 2018–20: CAGR > 0;
S > S del buy & hold; DD ≥ −35%; CAGR ancora > 0 togliendo i 2 trade migliori; e nel giudizio p ≤ 0,025 (due oggetti giudicati:
scelta e U; Bonferroni su 0,05), con p = quota di 500 serie 2024–26 rimescolate a blocchi di 20 giorni in cui la stessa regola ha
S ≥ quello reale. In più si riporta il p di selezione della scoperta (§5a).
Si riportano comunque: correlazione di rango (Spearman) di S fra scoperta e giudizio su tutte le regole e sulle valide; quota di
regole con CAGR > 0 e con S > buy & hold in giudizio e in conferma; risultati per lato, per intervallo dell'uscita (4h contro 1D),
EMA contro SMA; la sorte in giudizio delle prime 20 regole e delle prime 5 famiglie della scoperta.
**Confronto con W3.2** (radar/weekly.py su f_repo; 2018–20 su f_long), stessi periodi, ogni periodo da 10.000 $. Dichiarato: W3.2
è stata costruita vedendo tutto il 2021–26, quindi il suo 2024–26 non è fuori campione; la regola scelta sì.
**Uso complementare dentro W3.2** (3 varianti, fissate ora; stato della regola letto alla chiusura giornaliera, esecuzione
all'apertura del giorno dopo; rientro alla prima domenica con segnale W3.2 valido):
- K1: uscita aggiuntiva quando lo stato d'uscita della regola scelta è contro la posizione + ingresso W3.2 solo con stato a favore.
- K2: solo il filtro d'ingresso (ingresso W3.2 solo con lo stato della regola scelta a favore); uscite di W3.2.
- K3: come K1 con lo stato dell'esempio dell'utente (4h, 2 chiusure, EMA50).
Se la regola scelta ha uscita ATR (nessuno stato), K1 e K2 usano lo stato del suo regime. Una variante K conta solo se batte W3.2
in CAGR/DD sia nel 2021–23 sia nel 2024–26 e non peggiora il 2018–20.

## 7. PARTE A · atlante descrittivo (dopo la scelta; 2018–20, 2021–23, 2024–26)
Intervalli 4h, 1D, 1W; medie EMA/SMA 20, 50, 100, 200 (1W anche 21 e 40). Eventi, ciascuno al rialzo e al ribasso:
1. primo attraversamento in chiusura; 2. N = 2 e N = 3 chiusure consecutive oltre la media (barra in cui il conteggio arriva a N);
3. incrocio fra medie 20/50 e 50/200 (EMA e SMA); 4. pendenza che gira (segno di media − media di 5 barre prima);
5. stiramento: distanza chiusura/media − 1 che entra oltre il 95° o sotto il 5° percentile della propria storia precedente
(espansiva, minimo 500 barre; 1W minimo 100); 6. ritest: dopo ≥ 5 chiusure consecutive sopra la media, minimo ≤ media e
chiusura > media (specchio: massimo ≥ media e chiusura < media dopo ≥ 5 chiusure sotto); 7. allineamento: chiusura sopra (sotto)
la media dello stesso tipo e periodo su tutti e tre gli intervalli (periodi 20, 50, 200; EMA e SMA): ingresso nello stato e stato.
Misure per evento e periodo: casi, casi indipendenti (distanti ≥ 30 giorni), rendimento medio e mediano a 1, 3, 7, 14, 30 giorni
dalla chiusura dell'evento, eccesso sulla media incondizionata dello stesso periodo, quota di positivi, durata mediana dello stato
(fino all'evento opposto), falsi segnali (chiusura tornata dall'altro lato entro 3 e entro 10 barre).
**Ricorrente** = eccesso medio dello stesso segno in tutti e tre i periodi a 7 E a 30 giorni, con ≥ 5 casi indipendenti per periodo.
Placebo: 1.000 traslazioni circolari casuali delle date dell'evento dentro ciascun periodo (conserva il raggruppamento degli
eventi); p a due code sull'eccesso a 7 e a 30 giorni sull'intero 2018–26. Numero di test dichiarato nel README (ordine: ~500
eventi × 2 orizzonti); si riportano p grezzo, soglia di Bonferroni e quanti la superano. Le "credenze comuni" da verificare
(fissate ora): golden/death cross 50/200 1D; chiusura sopra/sotto SMA200 1D; EMA meglio di SMA; 2–3 chiusure di conferma meglio
di 1; ritest della media che tiene = continuazione; stiramento estremo = rientro; allineamento dei tre intervalli = continuazione;
pendenza che gira; perdita della EMA20/21 1W = fine del trend; SMA200 1W come pavimento.

## 8. Cosa NON si fa
Nessuna modifica a radar/, tests/ o al tool. Nessuna ricerca della combinazione che salva il risultato: se la regola scelta non
supera i criteri il verdetto è negativo. Parametri vicini e mappe servono a descrivere, non a scegliere di nuovo.
