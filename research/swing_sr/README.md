# Swing su supporti/resistenze settimanali, stop 5–10% e TP 10–15% · BTC · 22/11/2026

**Verdetto: la strategia swing NON è valida e non migliora il portafoglio.** La configurazione scelta sul 2014–20 porta 10.000 $
a 5.626 $ dal 2021 (DD −55,8%) e fallisce tutti e cinque i criteri preregistrati (PREREG 854ebff). Nessuna delle 405
configurazioni batte W3.1 (27.190 $, DD −9,8%) né il buy & hold (22.594 $). Il conto 70% W3.1 + 30% swing fa peggio di W3.1 da
sola. W3.1 resta invariata; nessuna modifica al tool.

## Cosa è stato provato
Stile richiesto dall'utente: posizioni brevi, stop 5–10%, take profit 10–15% o di più se il movimento ha forza, livelli di
supporto e resistenza. Tradotto in regole meccaniche (dettaglio nel docstring di `sw_engine.py`):
- **Livelli**: massimi e minimi di swing delle candele settimanali (3 settimane per lato), validi 104 settimane.
- **Ingresso** (segnale alla chiusura giornaliera, ingresso all'apertura successiva): B rimbalzo sul supporto · X rottura della
  resistenza · T ritest del livello rotto. Short speculari.
- **Regime**: R0 nessuno · R1 trend settimanale di solo prezzo · R2 condizioni d'ingresso di W3.1 (con flusso perp).
- **Lato**: solo long · solo short · entrambi.
- **Stop**: ST oltre il livello, limitato a 5–10% · SS oltre il livello, minimo 2% · SF fisso 7,5%.
- **Uscita**: T10 · T15 · TSR livello successivo · TH metà a +10% e metà con trailing · TT solo trailing.
- 3 × 3 × 3 × 3 × 5 = 405 configurazioni. Esposizione 1x, long spot e short perp, costi di W3.1, funding reale.

Metodo: parametri scelti solo sul 2014-06 → 2020-12, giudizio una sola volta sul 2021-01 → 2026-11 (10.000 $). Dati congelati
`research/p2_nuovi`. Esecuzione: `python3 sw_count.py` (conteggi), `python3 sw_run.py` (~30 s) → `risultati.txt`, `griglia.csv`,
`trade_scelta.csv`, `placebo.csv`, `equity.csv`.

## Risultati (2021-01-01 → 2026-11-15, 10.000 $)
| Strategia | Finale | CAGR | DD | CAGR/DD | Trade | WR | PF | IS 21–23 | OOS 24–26 |
|---|---|---|---|---|---|---|---|---|---|
| **W3.1 (in uso)** | **27.190** | 18,6 | −9,8 | 1,903 | 13 | 92 | — | 17.879 | 15.228 |
| Buy & hold | 22.594 | 14,9 | −76,6 | 0,19 | — | — | — | — | — |
| **S\* scelta sul 2014–20** (X/R1/LS/SS/TSR) | **5.626** | −9,3 | −55,8 | −0,17 | 88 | 23 | 0,83 | 7.025 | 8.008 |
| Mediana delle 405 | 7.753 | — | −46 | — | 34 | 30 | 0,90 | — | — |
| Mediana R0 (senza regime) | 5.716 | — | −64 | — | 70 | 30 | 0,87 | — | — |
| Mediana R1 (trend di prezzo) | 6.592 | — | −47 | — | 34 | 25 | 0,76 | — | — |
| Mediana R2 (condizioni W3.1) | 10.618 | — | −22 | — | 13 | 38 | 1,30 | — | — |
| Migliore a posteriori (B/R2/LS/SF/TSR)* | 21.611 | 14,0 | −19,6 | 0,72 | 20 | — | 2,86 | 13.984 | 14.261 |
| 70/30 W3.1 + S\* | 20.721 | 13,2 | −16,8 | 0,788 | — | — | — | — | — |
| 70/30 W3.1 + migliore a posteriori* | 25.516 | — | −9,7 | 1,784 | — | — | — | — | — |
| 70% W3.1 + 30% liquidità | 22.033 | — | — | — | — | — | — | — | — |

*Scelta guardando il 2021+: non utilizzabile, riportata solo come limite superiore. Perdita massima per trade: −8,6% (S\*),
mediana delle peggiori −6/−8% secondo il regime. S\* per anno: 2021 +4,4% · 2022 −25,5% · 2023 −9,7% · 2024 +21,4% · 2025 −27,1% ·
2026 −9,5%. S\*: 68 uscite in stop (media −3,6%), 20 in TP (media +10,1%); durata mediana 2 giorni.

## Criteri di S\* (tutti falliti)
1. Finale > 10.000 $ e PF ≥ 1,2 in IS e OOS: no (PF 0,82 / 0,85).
2. DD entro −20%: no (−55,8%).
3. Placebo (1.000 simulazioni con ingressi a caso nello stesso regime, stesso lato, stessi stop e uscita): p = 0,43; il placebo
   fa 5.189 $ in mediana contro 5.626 $.
4. Senza i 2 trade migliori: 3.870 $.
5. Vicini: 0 su 4 positivi (K = 2: 3.456 $; K = 4: 5.507 $).

## Cosa dicono i dati
- **La scelta sul passato non regge.** Solo 3 configurazioni su 405 erano ammissibili nel 2014–20 e nessuna è positiva dal 2021.
  La correlazione di rango fra CAGR/DD del 2014–20 e del 2021+ è −0,02 (201 configurazioni).
- **I livelli non danno il momento d'ingresso.** Gli ingressi sui livelli non si distinguono da ingressi casuali nello stesso
  regime (p = 0,43 per S\*; p = 0,23 per la migliore a posteriori, soglia di Bonferroni 0,00012).
- **Conta il regime, non il livello.** Solo R2 è positivo in mediana (70% delle configurazioni sopra 10.000 $). Ingressi casuali in
  R2 con stop 7,5% e TP al livello successivo fanno 16.487 $ in mediana: quel guadagno è il regime di W3.1, già in portafoglio
  (correlazione settimanale con W3.1 0,56).
- **Lo stile "breve" costa.** Dentro lo stesso regime, tagliare a +10/15% e uscire al 5–10% rende 10.000–14.400 $ in mediana
  contro i 27.190 $ di W3.1 che tiene la posizione: il TP ferma i pochi movimenti grandi che fanno il rendimento (W3.1: 3 trade
  = 59% del totale).
- **Stop.** Lo stop oltre il livello è sotto il 5% nel 79% dei segnali: il vincolo "5–10%" rende lo stop di fatto fisso al 5%.
  Finale mediano 2021+ per stop: SS 7.894 $ · ST 7.871 $ · SF 7.425 $: nessuna differenza utile.
- **Uscite.** Finale mediano: TH 8.413 $ · TT 8.367 $ · T10 7.425 $ · T15 7.295 $ · TSR 6.601 $. In R2 il TP al livello successivo è
  il migliore (12.300–14.400 $) e il TP a +15% il peggiore (9.200–10.200 $), ma con 13 trade mediani è un'indicazione, non un
  risultato.
- **Short.** Mediana 7.495 $, positive il 15%: lo short di breve durata sui livelli perde in ogni regime tranne R2 (9.908 $).

## Revisione critica (agente separato, sola lettura)
Nessun errore bloccante; il verdetto regge. Verifiche eseguite dal revisore con script propri, non salvati nel repo:
- 7 trade ricalcolati a mano (5 di S\*, 2 short di un'altra configurazione): coincidono.
- Stop e TP nello stesso giorno: 0 casi nel 2021+; invertire la regola non cambia nulla.
- A costi zero: S\* 7.595 $, mediana 8.997 $, 152 positive, massimo 24.471 $ (ancora sotto W3.1). La perdita non è solo costi.
- Stop minimo di S\* allargato a 3 / 4 / 5 / 7,5%: 5.110 / 5.239 / 3.831 / 3.926 $. Lo stop stretto non è la causa.
Difetti segnalati:
- Criterio 5: la tolleranza non agisce sugli ingressi X, quindi due dei quattro vicini erano identici a S\*. Senza effetto (0/4).
- Soglia di DD in ammissione (−30%) più larga di quella del giudizio (−20%).
- R2 escluso dalla scelta per costruzione (nessun flusso nel 2014–17): dichiarato nel PREREG.
- TH: dopo la metà a +10% lo stop a pareggio non è verificato nello stesso giorno e ignora i costi (lieve ottimismo, non tocca S\*).
- Funding addebitato il giorno d'ingresso e non quello d'uscita (trascurabile). Etichetta "stop" per un trailing in perdita.

## Deviazioni dal PREREG
1. `sw_run.py` è stato committato insieme ai risultati, non prima. Motore e PREREG non sono cambiati dopo i risultati.
2. Filtro "≥ 20 trade" nella parte descrittiva (correlazione di rango e migliori a posteriori): non era nel PREREG.
3. K = 3 fissato sui conteggi dei segnali, che includono il 2021–26 (nessun rendimento).
4. Correlazione di rango calcolata sui ranghi con Pearson (scipy non installato): equivalente a Spearman.
5. **Secondo ciclo non eseguito**: nessun errore del motore e nessuna ipotesi nuova dalla diagnosi (revisore contrario).

## Cosa significa per l'operatività
- Con questi dati non esiste una versione "swing breve su supporti e resistenze" che convenga affiancare a W3.1, né al 30% né
  in altra quota: la quota swing rende meno della liquidità (20.721 $ contro 22.033 $ con il 30% fermo).
- Stop 5–10% e TP 10–15% applicati agli stessi momenti in cui W3.1 è attiva rendono circa la metà di W3.1.
- I livelli restano utili come mappa (dove mettere un ordine, dove aspettarsi reazione), non come segnale.
- Limiti dello studio: barre giornaliere (nessun ingresso intragiornaliero sul livello), una sola definizione di livello, 13–34
  trade per le configurazioni R2. Il verdetto è "nessun vantaggio dimostrabile", come nelle lezioni 75–77, 95 e 105.

## Lezione proposta per RESEARCH.md
**Lezione 106**: lo swing breve sui livelli settimanali (rimbalzo, rottura, ritest) con stop 5–10% e TP 10–15% non funziona su BTC
dal 2021: la configurazione scelta sul 2014–20 fa 10k → 5,6k (DD −56%), 0/405 battono W3.1 o il buy & hold, gli ingressi sui
livelli valgono quanto ingressi a caso (p 0,43) e la classifica del 2014–20 non predice il 2021+ (rango −0,02). L'unico
guadagno viene dal regime di W3.1, e dentro quel regime il TP breve dimezza il rendimento. Il 70/30 peggiora W3.1. Non
riproporre swing su S/R con barre giornaliere; un criterio sui vicini va definito su parametri che agiscono sull'ingresso scelto.
