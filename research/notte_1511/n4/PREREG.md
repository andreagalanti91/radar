# N4 · Flussi di denaro, probabilità long/short e range S/R — preregistrazione
Scritta il 15/11/2026 prima di guardare qualsiasi risultato. Dati: data/*.csv del repo (spot Binance, perp Binance/OKX,
funding, metrics) + OI orario Binance 2021-01→2021-11 dalla cache /tmp/radar-work/liqfasce/work/h.pkl (stesso dato di metrics.csv,
rapporto 1,000). Periodo dal 01/01/2021; IS = 2021-01-01→2023-12-31, OOS = 2024-01-01→ultimo giorno con orizzonte completo.

## A · Probabilità condizionate
Rendimento futuro r_h = close(t+h)/close(t) − 1, h = 7, 14, 30 giorni (spot Binance, ingresso alla chiusura di t).
Informazione al giorno t: prezzo e medie alla chiusura di t; flussi, funding, OI e liquidazioni del giorno t−1 (shift 1, come live_flow).
Variabili (livelli fissi, scelti ora):
1. REG regime W3 dell'ultima settimana chiusa (W-SUN ≤ t): L = close > SMA40w ed EMA20w in salita; S = close < SMA40w, SMA40w
   sotto quella di 4 settimane prima, EMA20w in calo; N = altrimenti (stesse formule di radar/weekly.py).
2. PFs segno di pf14z (>0 / ≤0); PFt terzili fissi di pf14z: < −0,43 / −0,43…0,43 / > 0,43.
3. SFs, SFt: idem con sf14z.
4. DIV = sf14z − pf14z: < −0,5 (guida il perp) / ±0,5 / > +0,5 (guida lo spot).
5. FUND funding_z (z a 180 g della media 7 g del funding): ±0,43.
6. OI z a 180 g della variazione 7 g dell'OI (USD): ±0,43.
7. LIQ proxy: giorno di liquidazione se Δlog OI giornaliero ≤ −2·σ(180 g); "long" se il prezzo del giorno scende, "short" se sale.
   Stato = negli ultimi 3 giorni solo giorni long (LL) / solo short (LS) / nessuno o misti (0).
8. DSMA close/SMA40w − 1: < 0 / 0…+20% / > +20%.
9. DEMA close/EMA21w − 1: < −5% / ±5% / > +5%.
Celle = tutte le combinazioni di 1–3 variabili diverse (PFs e PFt non insieme; SFs e SFt non insieme).
Ammissibilità: ≥ 40 osservazioni non sovrapposte a 7 giorni (selezione greedy con passo 7) sul totale e ≥ 15 in IS e in OOS.
Sovrapposizione a 14/30 giorni: inferenza con bootstrap a blocchi mobili (blocco 30 giorni, 2.000 repliche) sulla serie giornaliera
(appartenenza alla cella, rendimento futuro) ricampionata insieme.
Statistiche per cella × h × periodo: n giorni, n indipendenti, media r_h, P(r_h > 0), eccesso rispetto alla media del periodo,
IC 95% bootstrap, p unilaterale (long: eccesso > 0; short: eccesso < 0).
Selezione: test IS su tutte le celle × 3 orizzonti × 2 lati, Benjamini–Hochberg q = 0,10 → candidati. Conferma OOS: stesso segno,
p OOS < 0,05; per i long P(>0) OOS sopra la base OOS; per gli short media OOS < 0 e P(>0) OOS < 0,5. In più BH q = 0,10 sui test
OOS dei soli candidati. Classifica: minimo fra z IS e z OOS (eccesso / errore bootstrap). Top 5 long e top 5 short (celle distinte).
Placebo globale: 50 sfasamenti circolari casuali (≥ 180 giorni) delle variabili rispetto ai rendimenti, stessa procedura; il numero
di celle confermate reali deve superare il 95° percentile del placebo.
Traduzione in trade (≤ 8 varianti): migliore cella long e migliore short (orizzonte della classifica) → in cella e flat: ingresso alla
chiusura, uscita dopo h giorni; long spot 0,1%/lato, short perp 0,05%/lato + funding, slippage 0,1%; 10.000 $ a 1x dal 2021.
Varianti: soglie ±0,30 e ±0,60 al posto di ±0,43/±0,5 (vicini), orizzonte h/2 e 2h. Robustezza: 2021–23/2024–oggi, senza il
trade migliore, placebo (ingressi casuali, stesso numero di trade e stessa durata, 1.000 estrazioni).
Soglie del verdetto: "utilizzabile come contesto forte" se confermata OOS, placebo globale superato e la versione trade batte il
buy & hold in MAR in entrambe le metà (long) / guadagna in entrambe le metà (short), con vicini dello stesso segno.
Altrimenti solo descrizione. Nessuna modifica a W3 in ogni caso (eventuale proposta separata).

## B · Supporti e resistenze
Livelli = radar/levels.compute sui dati fino alla domenica t (nessun dato futuro: i pivot sono confermati solo dopo k barre),
un'istantanea per settimana dal 03/01/2021. Zona di test = [lo − 0,25·ATR, hi + 0,25·ATR] (ATR giornaliero alla data).
Tipi: G = solo pivot giornalieri; W = contiene un pivot settimanale; V = solo nodo di volume; F = forza del tool ≥ 4 (sovrapposto).
Distanza del centro della zona dalla chiusura: 0–3%, 3–8%, 8–15% (zone che contengono il prezzo escluse).
Tocco: primo giorno entro 56 giorni con low ≤ alto zona (supporto) / high ≥ basso zona (resistenza).
Esito dopo il tocco (giorno τ):
- D3 giornaliero x = y = 3%: tenuta se entro 30 giorni (da τ+1) il massimo supera alto zona ·(1+x) prima di una chiusura
  sotto basso zona ·(1−y) (rottura controllata da τ); stesso giorno → rottura (prudente). Speculare per le resistenze.
- D6 giornaliero x = y = 6%, stessa regola.
- W10 settimanale x = y = 10%: candele settimanali, tocco entro 8 settimane, esito entro 12 settimane, rottura sulla chiusura settimanale.
Placebo: per ogni zona reale 20 zone casuali stesso lato, stessa larghezza, distanza uniforme nella stessa fascia, stessa istantanea.
Confronto P(tenuta | tocco) reale − casuale; IC e p con bootstrap a grappoli per mese dell'istantanea (2.000 repliche); BH q = 0,10
su tutti i test (4 tipi × 3 distanze × 3 scale × 2 lati). Soglia "vantaggio": ≥ +5 punti, BH superato e stesso segno ≥ +3 punti
in entrambe le metà. Atteso (lezioni 68, 75–77, 84): nessun vantaggio.
Range di oggi: radar/levels.compute sui dati fino al 14/11/2026 con la statistica storica del tipo × distanza (D3, D6, W10).
