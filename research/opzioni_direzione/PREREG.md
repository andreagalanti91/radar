# PREREG · Opzioni e direzione di BTC (skew, put/call, DVOL, massimo dolore, scelta put/call) · 27/11/2026

Domanda dell'utente: "C'è modo di capire la direzionalità di prezzo BTC in base alle opzioni? Ha mai seguito le scadenze (max
pain)? È uno strumento valido? Se volessi operare in opzioni, quando conviene prendere una put o una call?"

Questo file è scritto **prima** di calcolare qualsiasi relazione fra indicatori e rendimenti futuri (fase 1: solo dati e
conteggi, `conteggi.txt`). Va committato da solo, prima di eseguire gli script della fase 2. W3.2 (`radar/weekly.py`) non si
tocca: l'esito può essere solo contesto in dashboard o una proposta da presentare all'utente.

**Cosa è già escluso (non si ripete):** skew e VRP come filtri dei segnali di W3 (research/p2_nuovi, O1/O3, lezione 100); DVOL
o VIX come filtro di W3.1 (lezione 104); segnali di opzioni indipendenti F3 a–f, strutture, uscite e rinnovi contro B0r
(research/opzioni_studio, lezione 122); effetto calendario delle scadenze mensili (research/opex: nessun effetto robusto).
**Cosa è nuovo qui:** (1) skew, put/call e DVOL come **predittori della direzione** di BTC a 7/30 giorni, non come filtri di
W3; (2) il **massimo dolore** storico, mai testato perché "non ricostruibile": qui con un proxy dichiarato e validato
sull'open interest vero di oggi; (3) il **costo** dell'opzione (volatilità implicita contro realizzata) come criterio per
comprare o no la call/put di B0r, motivo che non valeva per i filtri su spot.

## Dati (fase 1, vedi `conteggi.txt`)
- **DVOL** Deribit BTC ed ETH, giornaliero e orario, dal 2021-03-24 (API pubblica `get_volatility_index_data`; prima non esiste).
- **Domeniche intere**: tutti gli scambi di opzioni Deribit BTC ed ETH di ogni domenica UTC dal 2021-01-03 al 2026-11-22 (308
  domeniche, con il lato dell'aggressore), `scarica.py domeniche`. Allineate alla decisione di W3.2 (chiusura della domenica).
- **Conteggi BTC dal 2021** (ETH simile): RR25 285 domeniche su 308, PC 308, DVOL 296 (dal 28/03/2021), ΔDVOL 295; IS circa
  145 domeniche, OOS circa 140; massimo dolore 70 scadenze (36 IS, 34 OOS). DVOL orario completo salvo 1 ora (2026-11-20 20:00).
- **Campione giornaliero** già scaricato (`research/opzioni_studio/dati/cache`: 3 finestre da 1000 scambi alle 00/08/16 UTC,
  BTC, dal 2018; dal 2021 il giorno non è mai intero). Riutilizzato per il put/call settimanale (vicino) e per il proxy del
  massimo dolore.
- **Open interest per strike**: le API pubbliche non lo danno all'indietro; Tardis (giorno gratuito di ogni mese) non è
  accessibile (limite di trasferimento raggiunto). Unico open interest vero: l'istantanea di oggi (`book_BTC_2026-11-27`) e
  `data/opex/snap.jsonl` (dal 26/11/2026).
- **Prezzi**: `data/spot.csv` (BTC, chiusura giornaliera Binance, = 24:00 UTC), `data/eth_spot.csv`, `research/opzioni_studio/
  cache/btc_0800.csv` e `btc_1h.csv` (apertura delle 08:00 UTC, regolamento), `data/funding.csv` (short in perp). Fine dati:
  2026-11-21 (BTC giornaliero).

## Definizioni (uniche, fissate ora)
Decisione alla **chiusura della domenica (24:00 UTC)** con dati fino a quell'istante. Rendimenti futuri: r7 = ln(chiusura di
D+7 / chiusura di D), r30 = ln(chiusura di D+30 / chiusura di D), D = domenica; un'osservazione senza D+h nei dati si scarta.
1. **Skew 25-delta (RR25)**: scadenza con 20–50 giorni dalla domenica 24:00 più vicina a 30 (pari: la più corta). Per ogni
   scambio della domenica: delta Black-76 con F = prezzo indice Deribit dello scambio, T dallo scambio alla scadenza (08:00
   UTC), σ = IV dello scambio. IV_P25 = mediana pesata per quantità delle IV delle put con delta in [−0,35; −0,15]; IV_C25 =
   delle call con delta in [0,15; 0,35]; minimo 5 scambi per lato, altrimenti mancante. **RR25 = IV_P25 − IV_C25** (punti di
   volatilità; > 0 = put più care = paura). Approssimazione dichiarata: fascia di delta invece di interpolazione al 25 esatto;
   F = indice invece del future.
   Buco strutturale: 23 domeniche BTC su 308 (la prima dopo la scadenza mensile, ogni 1–3 mesi) non hanno una scadenza fra 20 e
   50 giorni → RR25 mancante, l'osservazione si scarta (nessun riempimento).
2. **Put/call (PC)**: quantità (BTC) di put scambiate / quantità di call scambiate, tutte le scadenze, domenica intera.
3. **DVOL**: chiusura giornaliera della domenica; **ΔDVOL = ln(DVOL_D / DVOL_{D−7})**.
4. **Volatilità realizzata futura** RV30 = deviazione standard dei rendimenti logaritmici giornalieri da D+1 a D+30 × √365 ×
   100; passata RV30p = stessa misura da D−29 a D.
5. **Massimo dolore (proxy, solo BTC)**: per ogni scadenza mensile E (ultimo venerdì del mese, 08:00 UTC) dal 2021-01 al
   2026-10 (70 scadenze, 23 trimestrali), pseudo open interest per strike e tipo = quantità del campione giornaliero **negli
   ultimi 28 giorni** fino al giorno E−8 compreso (dati fino alle 00:00 di E−7). MP7 = strike quotato che minimizza
   Σ_call q·max(0, X−K) + Σ_put q·max(0, K−X) (stessa formula di `radar/opex.py`). **Limite**: il volume non è open interest
   (le chiusure contano come aperture). Scelta del proxy con una regola sulla sola qualità dei dati, senza rendimenti: fra
   "cumulato dalla quotazione" e "ultimi 28 giorni" vale quello con l'errore mediano più basso contro il massimo dolore da
   open interest vero delle scadenze aperte oggi (`conteggi.txt`): 28 giorni 3,25 punti % del prezzo contro 4,06; stesso lato
   rispetto al prezzo 8/8 per entrambi; il proxy tende a stare sopra il vero (6–7 casi su 8). Il cumulato resta un vicino.
   La validazione è su 8 scadenze di un solo giorno: il proxy resta un'approssimazione e H4 un test del proxy, non del
   massimo dolore vero.
   S7 = apertura BTC delle 08:00 di E−7; ST = apertura delle 08:00 di E (regolamento). Specchio L = S7²/MP7 (livello alla
   stessa distanza logaritmica dal lato opposto).
6. **VRP** = DVOL_D / RV30p_D.

## Periodi
IS 2021-01-01 → 2023-12-31; OOS 2024-01-01 → fine dati. Le soglie (terzili, segno) si stimano solo su IS. Le osservazioni con
DVOL partono dal 2021-03-28.

## Ipotesi e varianti (8, famiglia di Holm a α 0,05 su BTC)
Per V1–V6 la statistica è la correlazione di Spearman fra indicatore e misura futura sulle domeniche; il segno atteso è quello
stimato in IS (nessuna ipotesi di verso a priori: contrarian o tendenza lo decide l'IS); p OOS a una coda nel verso IS con
**placebo a slittamento circolare** (serie dell'indicatore spostata di k settimane, k uniforme in [8, n−8], 10.000 prove, seme
20261127), che conserva l'autocorrelazione e la sovrapposizione dei rendimenti a 30 giorni.

| V | Ipotesi | Indicatore → misura |
|---|---|---|
| V1 | H1 skew → direzione 7 g | RR25 → r7 |
| V2 | H1 skew → direzione 30 g | RR25 → r30 |
| V3 | H2 put/call (contrarian o tendenza) 7 g | PC → r7 |
| V4 | H2 put/call 30 g | PC → r30 |
| V5 | H3 variazione DVOL → direzione 30 g | ΔDVOL → r30 |
| V6 | H3 livello DVOL → ampiezza 30 g | DVOL → RV30 (controllo positivo: atteso ρ > 0) |
| V7 | H4 il prezzo converge al massimo dolore nell'ultima settimana | vedi sotto |
| V8 | H5 put/call di B0r solo se l'opzione non è cara | vedi sotto |

**V7 (H4).** Per ogni scadenza: convergenza c_MP = |ln(S7/MP7)| − |ln(ST/MP7)| (> 0 = il prezzo si è avvicinato) e c_L con lo
specchio L. Statistica: media di (c_MP − c_L) su tutte le scadenze; p a una coda (> 0) con segni casuali (10.000, seme
20261127); placebo aggiuntivo: MP7 sostituito da uno strike quotato a caso della stessa scadenza entro ±15% da S7 (10.000,
stesso seme). Si riporta anche la quota di scadenze in cui il prezzo si muove verso MP7. Sul totale 2021–26 (≈ 70 scadenze) e
per periodo; il p di Holm è quello OOS.

**V8 (H5).** B0r esatto come in `research/opzioni_studio` (motore `op_engine.py`, prezzatore della superficie, finestra 20–50
giorni, alla pari, 5% del conto, vendita all'uscita di W3.2), dal 2021. Filtro: si salta l'operazione se il VRP della domenica
del segnale supera il 75° percentile dei VRP domenicali IS. p: test appaiato a segni casuali sulle operazioni (filtrate = 0
contro il risultato di B0r). Con meno di 20 operazioni per metà V8 è **descrittivo** per costruzione (come nello studio
opzioni) e non può essere promosso; resta nella famiglia di Holm.

## Traduzione in regola operativa (per V1–V5 e V7; 10.000 $, 1x, costi inclusi)
- **R(X)** per V1–V5: ogni domenica, posizione per la settimana successiva (dal lunedì 00:00 alla domenica 24:00): long spot 1x
  se s·X è nel terzile alto IS, short perp 1x se nel terzile basso, liquidità altrimenti (s = segno IS di V). Ritenzione fissa di
  7 giorni con rivalutazione settimanale anche per le varianti a 30 g.
- **R(V7)**: long 1x se MP7 > S7, short 1x se MP7 < S7, da E−7 08:00 a E 08:00; liquidità nel resto del mese.
- **Costi**: 0,10% del controvalore per lato a ogni cambio di posizione; funding Binance (`data/funding.csv`) sugli short;
  liquidità a rendimento zero. Valutazione giornaliera alla chiusura.
- Metriche per IS, OOS e dal 2021: capitale finale, rendimento, max drawdown giornaliero, operazioni, win rate, MAR
  (rendimento / |DD|), CAGR/DD; confronto con W3.2 com'è (`radar.weekly.simulate` dal 2021, continuo) e con il buy & hold.
  V8 con le metriche dello studio opzioni contro B0r.

## Robustezza (tutte riportate, nessuna scelta a posteriori)
- **Periodi**: IS e OOS separati (2021–23 / 2024–oggi), stesso segno richiesto.
- **Parametri vicini**: V1–V2 fascia di delta [0,20; 0,30], RR25/IV_ATM, z-score a 52 settimane; V3–V4 put/call del lato
  aggressore in acquisto e put/call del campione lun–dom (`pc_camp7`); V5 Δ a 14 giorni e orizzonte 7 g; V6 orizzonte 7 g;
  V7 riferimento E−3 e proxy "cumulato dalla quotazione"; V8 soglie 66° e 90° percentile. Per le regole: quartili e quintili invece dei
  terzili.
- **Senza il trade migliore** (e senza i due migliori) per ogni regola.
- **Placebo della regola**: posizioni slittate in modo circolare (10.000, seme 20261127), p sul MAR OOS.
- **Stessi parametri su ETH** per V1–V6 (DVOL ETH, domeniche ETH). V7 solo BTC (manca il campione ETH per strike).

## Criteri (fissati ora)
- **"Strumento valido" come indicatore di direzione** (V1–V5, V7), tutti insieme: (a) p OOS corretto con Holm su 8 < 0,05;
  (b) |ρ| OOS ≥ 0,10 (V7: quota verso MP7 ≥ 55% in OOS) e stesso segno in IS e OOS; (c) almeno 3 vicini su 4 con lo stesso
  segno in OOS; (d) ETH con lo stesso segno (p non corretto < 0,10) — non richiesto per V7.
- **"Strumento operativo"**: valido e inoltre R in OOS con MAR > buy & hold OOS, capitale > 10.000 $ senza i due trade migliori,
  placebo della regola p < 0,05. Anche se operativo, non sostituisce né modifica W3.2: si presenta all'utente come proposta.
- **V6** è un controllo positivo: se fallisce, la pipeline va ricontrollata prima di leggere le altre. Si riporta anche la
  mediana di DVOL/RV30 futura (> 1 = le opzioni costano in media più di quanto si muove BTC).
- **V8** "migliore di B0r" solo con i criteri dello studio opzioni (finale OOS > B0r con DD non peggiore di oltre 3 punti,
  sopra B0r senza le 2 migliori, vicini, ≥ 20 operazioni per metà, Holm): con le operazioni disponibili non è raggiungibile;
  il risultato serve solo a rispondere "quando conviene la call o la put".
- Nessun ritocco di definizioni, soglie o periodi dopo i risultati; ogni deviazione va dichiarata nel README.
