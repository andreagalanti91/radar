# PREREG · Swing su supporti/resistenze settimanali con stop 5–10% e TP 10–15% · BTC · 22/11/2026

Scritto e committato da solo PRIMA di calcolare qualsiasi rendimento. Finora eseguito solo `sw_count.py` (conteggi di segnali e
distanze degli stop, nessun P&L): `conteggi.txt`. Le regole operative sono nel docstring di `sw_engine.py` (committato dopo questo
file, senza modifiche alle regole).

## Domanda
Uno swing di breve durata su BTC, con ingressi sui livelli settimanali, stop al 5–10% oltre il livello e take profit al 10–15% (o
trailing se il movimento ha forza), è profittevole dopo i costi? Migliora un portafoglio 70% W3.1 + 30% swing rispetto a 100% W3.1?

## Cosa è già stato respinto (da non ripetere)
S/R come segnale su giornaliero e settimanale (lezioni 75–77, 97), struttura S/R long-only settimanale (nuova_strategia N1),
swing a tempo di 2–3 giorni (95), TP e stop in ATR su W3.1 (105). Qui è nuovo: segnali giornalieri su livelli settimanali, stop
in percentuale fissato dal livello, TP in percentuale o al livello successivo, parte con trailing, filtro di regime.

## Griglia (405 configurazioni, parametri fissi: K = 3, livelli attivi 104 settimane, tolleranza 1%, cuscinetto 1%)
- Ingresso: B rimbalzo sul supporto · X rottura della resistenza · T ritest del livello rotto (entro 20 giorni).
- Regime: R0 nessuno · R1 trend settimanale di solo prezzo · R2 condizioni d'ingresso di W3.1 (con flusso perp).
- Lato: L solo long · S solo short · LS entrambi (una posizione per volta; due segnali opposti lo stesso giorno = nessun trade).
- Stop: ST strutturale limitato a 5–10% · SS strutturale puro (minimo 2%, massimo 10%) · SF fisso 7,5%.
- Uscita: T10 · T15 · TSR livello successivo (5–30%, altrimenti 15%) · TH metà a +10% e metà con trailing 3 ATR14 giornalieri,
  stop almeno a pareggio · TT solo trailing 3 ATR14.
Esposizione 1x del conto (nessuna leva), long spot e short perp, commissioni 0,10% / 0,05% per lato, slippage 0,10% su ingressi a
mercato e stop, TP come ordine limite, funding reale sugli short. Stop e TP nello stesso giorno: vale lo stop.
K è stato fissato a 3 guardando solo i conteggi (K = 4 lascia 5–16 segnali per cella nel regime R1 in alcuni periodi).

## Scelta (solo 2014-06-01 → 2020-12-31, frame lungo; MAI sul 2021+)
Ammissibili: ≥ 40 trade, profit factor ≥ 1,2 sia nel 2014–17 sia nel 2018–20 (simulati separatamente), DD ≥ −30%.
**S\*** = configurazione ammissibile con il CAGR/DD più alto. Se nessuna è ammissibile lo si dichiara e S\* è quella con il
CAGR/DD più alto fra quelle con ≥ 40 trade. Si riportano anche le migliori ammissibili per ciascun tipo d'ingresso (finalisti),
ma il verdetto riguarda solo S\*. Limite noto: R2 non ha segnali nel 2014–17 (flusso assente) e sarà quasi certamente escluso
per numero di trade: resta descrittivo.

## Giudizio (2021-01-01 → 2026-11-15, frame del tool, 10.000 $; una sola volta)
S\* è **valida** se soddisfa tutti:
1. finale > 10.000 $ e profit factor ≥ 1,2 sia in IS 2021–23 sia in OOS 2024–26 (ciascuno riparte da 10.000 $);
2. DD massimo giornaliero non oltre −20%;
3. placebo: p ≤ 0,05 contro 1.000 simulazioni con ingressi a caso (stesso numero di trade per lato, giorni estratti fra quelli
   in cui il regime ammette quel lato, distanze di stop ricampionate dai trade veri, stessa gestione dell'uscita);
4. finale > 10.000 $ anche togliendo i 2 trade migliori;
5. vicini: almeno 3 su 4 fra K = 2, K = 4, tolleranza 0,5% e 2% chiudono > 10.000 $ con profit factor > 1.
S\* **migliora il portafoglio** se, oltre a 1–5, il conto 70/30 (7.000 $ in W3.1 + 3.000 $ in S\*, senza ribilanciamento) ha
CAGR/DD superiore a W3.1 da sola (1,903; 27.190 $, DD −9,8%). Riferimenti: W3.1, buy & hold, 70/30.

## Descrittivo (non cambia il verdetto)
Tabella delle 405 configurazioni sul 2021+; quota con finale > 10.000 $; correlazione di rango (Spearman) fra CAGR/DD del
2014–20 e del 2021+; la migliore del 2021+ è riportata come "scelta a posteriori, non utilizzabile", con placebo e soglia di
Bonferroni 0,05/405. Confronto ST / SS / SF e fra le cinque uscite a parità del resto (mediane), per rispondere alla domanda
dell'utente su stop e TP. Durata mediana dei trade, quota del tempo in posizione, perdita massima per trade.

## Secondo ciclo
Ammesso una sola volta, dopo la revisione critica di un agente separato, solo per: (a) un errore del motore; (b) una ipotesi
motivata dalla diagnosi dei trade perdenti. Addendum committato prima dell'esecuzione; i risultati del secondo ciclo sul 2021+
sono esplorativi (secondo sguardo agli stessi dati) e non possono da soli portare a un verdetto "valida".
