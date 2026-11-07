# Scout balene Hyperliquid · preregistrazione

Scritto il 2026-11-07 **prima** di guardare i risultati del primo ciclo (radar/scout.py). Le soglie e il punteggio qui sotto
sono fissi: si cambiano solo con una nuova versione datata di questo file, mai per far passare un wallet già visto.

## Obiettivo
Ogni giorno, i 3 wallet (conti personali o vault, cioè "copytrading" su Hyperdash) di Hyperliquid con:
crescita annua alta (> 80%), drawdown contenuto, poco funding pagato, crescita regolare, e almeno $1M nel conto.
Fonti: solo API pubbliche di Hyperliquid (le stesse che usa Hyperdash): classifica stats-data, elenco vault stats-data,
info `portfolio`, `userFunding`, `clearinghouseState`.

## Universo e prefiltro (economico, dalla classifica)
- conti della classifica con accountValue ≥ $1M, più i vault con TVL ≥ $1M (esclusi HLP e i suoi vault figli, vault chiusi);
- PnL allTime > 0 e ROI allTime > 50%; ROI 30 giorni > −10%; volume 30 giorni > 0 (attivo);
- esclusi i market maker: volume 30 giorni / valore del conto > 60 (rotazione da bot);
- i rimanenti ordinati per min(ROI allTime, 3) + ROI 30 giorni; si analizzano i primi 150 (più i wallet già scelti e quelli da
  seguire per la verifica).

## Metriche (ultimi 365 giorni, storia `portfolio` allTime ≈ un punto ogni 14 giorni)
- **rendimento 1 anno**: time-weighted, Modified Dietz per intervallo: r = ΔPnL / (valore iniziale + ½ flusso netto),
  flusso = Δvalore − ΔPnL (depositi e prelievi), concatenato. Con 300–365 giorni di storia si annualizza;
- **max drawdown**: sull'indice time-weighted (quindi in % del capitale, depositi esclusi), il peggiore fra la storia annua
  (14 giorni), quella mensile (~16 ore) e quella settimanale;
- **regolarità**: R² del log dell'indice contro il tempo; % di periodi (≈ 2 settimane) positivi; periodo più lungo sott'acqua;
- **funding**: somma di `userFunding` (fino a 365 giorni), costo netto pagato in % del PnL dello stesso periodo e del capitale;
- **quota perp**: PnL perp (perpAllTime) / PnL totale nell'anno;
- per i finalisti: valore del conto perp da `portfolio` contro la somma di `clearinghouseState` su tutti i DEX, e leva attuale.

## Filtri rigidi (livello 0)
| filtro | soglia |
|---|---|
| valore del conto | ≥ $1M |
| storia | ≥ 300 giorni, nessun buco > 35 giorni fra due punti, valori non negativi |
| coerenza | PnL allTime di `portfolio` entro il 10% (o $50k) da quello della classifica |
| attività | volume negli ultimi 30 giorni > 0 |
| quota perp | ≥ 50% del PnL dell'anno viene dai perp (trader copiabile, non un portafoglio spot) |
| rendimento 1 anno | > 80% |
| max drawdown | ≤ 30% |
| R² | ≥ 0,75 |
| funding pagato | ≤ 15% del PnL |
| verifica finale | valore perp `portfolio` vs `clearinghouseState` entro il 10% |

Se passano meno di 3 wallet si allenta, in quest'ordine, un passo alla volta (e la pagina lo dichiara):
1. R² ≥ 0,65; 2. max drawdown ≤ 35%; 3. funding ≤ 20% del PnL; 4. rendimento > 60%.
Valore, storia, coerenza, attività, quota perp e verifica finale non si allentano mai. Se anche al passo 4 i wallet sono
meno di 3, i posti vuoti restano vuoti (meglio 2 balene buone che una a caso).

## Punteggio (0–100)
Componenti in [0, 1]:
- rendimento/rischio = min(1, ln(1 + rend/max(DD, 5%)) / ln(21)), peso 0,40;
- R² = (R² − 0,5)/0,5 limitato a [0, 1], peso 0,25;
- % periodi positivi, peso 0,20;
- funding basso = 1 − min(1, costo funding/PnL ÷ 15%), peso 0,15.

## Scelta e isteresi
I 3 con il punteggio più alto fra chi passa. Un wallet già scelto resta finché passa i filtri, a meno che uno sfidante
abbia un punteggio di almeno il 15% più alto del più debole dei tre. Nomi stabili: "Balena 1–3" (posto fisso) o il nome del vault.

## Verifica e apprendimento
- ogni giorno si salva la fotografia (valore, PnL allTime) delle scelte, di tutti i wallet che hanno passato i filtri e di un
  campione fisso di 150 conti ≥ $1M della classifica;
- a 7, 30 e 90 giorni: rendimento Modified Dietz delle scelte contro la mediana di chi aveva passato i filtri e contro la
  mediana del campione ≥ $1M; drawdown delle scelte dalle fotografie giornaliere;
- ogni 30 giorni, solo con almeno 30 osservazioni a 30 giorni: correlazione di Spearman di ogni componente con il rendimento
  successivo; ogni peso si sposta al massimo di 0,05 per passo (minimo 0,05, somma 1). Prima di allora i pesi restano questi.

## Limiti noti
Punti allTime ogni ~14 giorni: il drawdown dentro le due settimane non si vede (in parte recuperato con le storie a 30 e 7
giorni). I vault includono i depositi dei follower: il Modified Dietz li neutralizza, ma non le commissioni del leader.
Un conto può avere sub-account o altri wallet: si vede solo l'indirizzo analizzato. Rendimento passato ≠ futuro.
