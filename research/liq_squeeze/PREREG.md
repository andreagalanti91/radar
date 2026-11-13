# Preregistrazione · ingresso da squilibrio delle liquidazioni ("squeeze") con fascia DCA · 13/11/2026

Scritta PRIMA di calcolare qualsiasi risultato. Soglie e regole non si cambiano dopo. Solo BTC.

## Idea dell'utente (13/11, mappa Coinglass)
Dopo la cascata del 13/11 sotto il prezzo restano poche liquidazioni long, sopra ~$1,2B di short fino a 76k: entrare long quando
i long sono stati "puliti" e sopra c'è molto carburante di short; simmetrico per gli short.

## Dati (nessun look-ahead)
- Candele 1h BTCUSDT (archivio perp Binance, poi spot Binance per le ultime ore) + OI orario Binance USDT-M (research/liq_fasce/lf_data.py).
- Mappa ricostruita OGNI ORA T con `radar/liqmap.build` sulle 504 ore che finiscono prima di T (`lf_data.map_at`): decisione con dati
  fino alla chiusura dell'ora T−1, ingresso all'apertura dell'ora T (barra successiva). Prezzo di riferimento p = chiusura T−1.
- Funding reale giornaliero (radar/features `funding`), pagato/incassato ora per ora (funding del giorno / 24) sulla parte aperta.
- Costi 0,08% per lato su ogni riempimento e ogni uscita (limit e mercato). Stop e target: se nella stessa ora si toccano stop e
  target vale lo stop; un'ora in cui si riempie un limit non tocca il target (solo lo stop).
- IS 2021-01-22 → 2023-12-31, OOS 2024-01-01 → oggi. Capitale 10.000 $, 1x (nozionale = 100% del capitale al segnale), una
  posizione alla volta; DD sul mark-to-market giornaliero.

## Definizioni
- Squilibrio S(T) = (short sopra − long sotto) / (short sopra + long sotto), entro ±6% da p. In [−1, +1].
- Fascia densa = cluster `liqmap.clusters` con rel ≥ 0,30 (come liqcascade/dashboard) entro ±10%.
- Cascata long (definizione di radar/liqcascade): discesa ≥ 3% in ≤ 8 ore che attraversa ≥ 2 fasce dense long della mappa
  all'ora di partenza. È nota alla chiusura della prima ora che la soddisfa; "nelle ultime 72h" = un'ora valida chiusa in (T−72h, T].
  Cascata short: simmetrica (salita ≥ 3%, fasce dense short).
- Pulizia long = cascata long nelle ultime 72h OPPURE long sotto (±6%) < 20° percentile delle ultime 2.160 ore (90 giorni, solo passato).
- ATR 4h = media a 14 barre del true range su candele 4h chiuse (00, 04, … UTC) prima di T.
- Fondo della fascia DCA F (long): fra i candidati sotto p a distanza 1–3% (prezzi delle fasce dense long e bordo alto delle zone di
  supporto `radar/levels.compute` del giorno prima) il più vicino a p; se nessuno, F = p·0,97.
- Stop = F − 1 ATR 4h. Target 1 = prima fascia densa short sopra p a ≥ 0,5% (metà posizione); target 2 = fascia densa short successiva
  a ≥ 0,5% oltre T1 (l'altra metà; se non c'è, la seconda metà esce a tempo). Se non c'è T1 entro +10%: nessun trade.
- Uscita a tempo: 5 giorni (120 ore) dall'ingresso/dal segnale. Lo stop non si sposta.

## Regole (6) e controlli
- **L1**: long se S ≥ 0,50 e pulizia; tutto a mercato all'apertura di T; stop, target e tempo come sopra.
- **L2**: come L1 ma con DCA: 3 limit (1/3 ciascuno) equidistanti fra p e F (p−(p−F)/3, p−2(p−F)/3, F), validi 24 ore; il trade esiste
  solo se si riempie almeno un limit; uscite come sopra (5 giorni dal segnale).
- **L3**: L2 senza pulizia (solo S ≥ 0,50).
- **S1**: short simmetrico di L2 (S ≤ −0,50, pulizia short, DCA sopra fino a +3%, stop sopra + 1 ATR, target fasce dense long sotto).
- **W3-DCA**: sugli ingressi di W3 (radar/weekly.simulate, 10k → ~78,5k) metà a mercato come W3, metà sulla fascia DCA (3 limit come L2
  dalla mappa del lunedì 00 UTC, validi 24 ore, la parte non riempita a mercato alla scadenza); uscite di W3 invariate. Short simmetrici.
- **Sizing** (riportato, non una regola in più): L2 e S1 con rischio 0,5% e 1% del capitale per trade (nozionale = rischio / distanza
  dallo stop medio, max 1x), (a) sempre, (b) solo quando W3 è flat.
- Controlli: (i) **momentum** con lo stesso schema di L1/L2/L3: segnale = rendimento 24h ≥ soglia scelta in modo che le ore-segnale
  siano tante quante quelle della regola nel IS (M+), e lo stesso con rendimento 24h ≤ soglia (M−, "compra la discesa");
  (i-b) **pulizia sola** (L2 senza condizione su S); (ii) placebo: a) stessi trade in ore casuali (1.000 estrazioni, stesso numero
  di trade, stesso schema, mappa di quell'ora), b) segnale da mappe di altri giorni (serie del segnale spostata circolarmente di
  30–700 giorni, 200 spostamenti); (iii) vicini: soglia 0,30/0,70, raggio ±4%/±8%, uscita 3/7 giorni, finestra di pulizia 48/96h,
  percentile 10/30, pulizia solo cascata / solo percentile; (iv) senza i 3 trade migliori; (v) IS/OOS.

## Criteri di accettazione (per regola, ACCETTATA per carta solo se TUTTI)
1. ≥ 30 trade dal 2021; 2. PF ≥ 1,2 e capitale finale > 10k a 1x, MAR > 0; 3. media per trade > 0 sia IS sia OOS;
4. OOS: media per trade > del migliore fra M+ e M− con la stessa frequenza; 5. placebo a) e b) p < 0,05/6 = 0,0083 (Bonferroni sulle
6 regole); 6. ≥ 2/3 dei vicini con PF > 1; 7. senza i 3 trade migliori capitale finale > 10k.
W3-DCA: accettata solo se batte W3 nel capitale finale E nel MAR sia 2021–23 sia 2024→ (lezione 92: l'all-limit perdeva).
Nessuna regola sostituisce W3; al massimo "per carta".

## Stato di oggi
Le stesse regole applicate all'ultima ora chiusa: setup L1/L2 sì/no, fascia DCA, stop, target, motivazione (modulo squeeze.py).
