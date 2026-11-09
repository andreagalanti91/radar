# Famiglia C · Flusso e derivati — preregistrazione (09/11/2026, scritta PRIMA di ogni backtest)

Regole comuni: research/intraday2/PIANO.md. Qui solo ciò che è specifico della famiglia C.

## Impostazione fissa (uguale per tutte le varianti)
- Timeframe **4h** (lezione 78: su 1h i costi valgono 0,1–0,2R a trade). Segnale alla chiusura, ingresso all'apertura successiva.
- Asset BTC, ETH, SOL, stessi parametri. Long e short simmetrici.
- Uscite di riferimento (PIANO): stop 1,5 ATR(14), TP1 +1,5R metà, stop a pareggio dopo TP1, TP2 +3R, uscita a tempo 12 barre.
  Nessuna uscita/inversione sul segnale opposto (`reverse_exit=False`).
- Sizing: rischio 1% dell'equity realizzata per trade, nozionale massimo 2x l'equity per posizione (leva isolata 2x per la
  liquidazione), esposizione totale massima 5x. Costi del motore (0,05% + slippage, funding reale).
- Dati: funding = ultimo tasso pubblicato (normalizzato a 8h), z-score su 180 barre (30 giorni). OI: `oi` (0 → NaN),
  variazione su 6 barre (24 h), z-score su 180 barre. Delta taker: dr_n = (2·taker_buy − volume)/volume su n barre (NaN → 0).
  L/S: `glob_acc_ls` (top_pos_ls escluso: 87% NaN nel 2022), z-score su 180 barre.
- Momentum di base M (controllo C0): long se close > massimo dei 20 high precedenti e EMA20 > EMA50; short speculare.

## Varianti (8 in totale, C0 compreso)
| id | idea | regola long (short speculare) | parametri |
|---|---|---|---|
| C0 | controllo: momentum senza flusso | M | n=20 |
| C1 | funding estremo + prezzo che cede (contrarian) | fz ≤ −2 in una delle ultime 6 barre e close > massimo dei 6 high precedenti | z=2, n=6 |
| C2 | momentum con funding non affollato | M e fz < +1 (short: fz > −1) | z=1 |
| C3 | rottura con OI in espansione (conferma) | M e z(ΔOI 6 barre) > +1 | z=1 |
| C4 | flush di OI dopo un grande movimento (capitolazione) | ret 6 barre ≤ −3 ATR, z(ΔOI 6) ≤ −2, barra verde (close > open) | k=3, z=2 |
| C5 | divergenza CVD vs prezzo (assorbimento) | close = minimo delle 20 chiusure e z(dr_20, 180 barre) ≥ +1 e barra verde | n=20, z=1 |
| C6 | L/S affollato, fade solo con conferma del prezzo | z(glob_acc_ls) ≤ −2 in una delle ultime 6 barre (retail short) e close > massimo dei 6 high precedenti | z=2, n=6 |
| C7 | punteggio di flusso come filtro di M | M e tutti: dr_6·side > 0, z(ΔOI 6) > 0, fz·side < 2 | — |

Disponibilità dei dati: C0, C1, C2, C5 dal 2021-01 (warm-up dal 2020-09). C3, C4, C7 usano l'OI → campione dal **2021-12**
(in campione effettivo 2021-12 → 2023-12, 25 mesi). C6 usa `glob_acc_ls` → dal **2021-12** (2022 al 95%).
I segnali che richiedono un dato mancante non scattano (nessun riempimento).

## Scelta (solo 2021–2023) e giudizio (2024 → oggi, una volta)
- Candidata in campione se: PF ≥ 1,2, aspettativa ≥ +0,10R, positiva su ≥ 2/3 asset, 2–12 trade/mese totali.
- Le varianti filtro (C2, C3, C7) devono anche battere C0 in campione su aspettativa R.
- Fra le candidate si sceglie quella con aspettativa R più alta in campione; si scrive la scelta qui sotto PRIMA di aprire il
  fuori campione. Il fuori campione si calcola poi per tutte (trasparenza), ma "passa" solo una candidata in campione con
  TUTTI i 7 criteri di PIANO.md sul 2024→oggi.
- Placebo: 500 giri sul fuori campione (`engine.placebo`, stessi lati/frequenza/stop/uscite); serve percentile > 90 su ret_pct.
- Vicini: one-at-a-time ×0,8 e ×1,2 su ogni parametro della tabella (interi arrotondati); la mediana del rendimento fuori
  campione dei vicini deve essere > 0.
- Senza il trade migliore: somma PnL fuori campione meno il trade migliore > 0.
- Confronto: buy & hold a pesi uguali BTC/ETH/SOL (1x) e W2 + MACD (numeri da RESEARCH.md).
- Se nessuna variante passa lo si scrive chiaramente; nessuna seconda tornata di varianti su questo stesso campione.

## Emendamento (prima di vedere risultati di C5)
C5 come scritta dava 0 trade per costruzione (barra verde ⇒ close > close precedente ⇒ non può essere il minimo delle
20 chiusure). Correzione meccanica: "low della barra = minimo dei 20 low" (high = massimo dei 20 high per lo short); resto uguale.

## Scelta in campione (compilata dopo il solo 2021–23, prima del fuori campione)
Nessuna variante è candidata: nessuna ha PF ≥ 1,2 e +0,10R. La più vicina è C6 (L/S affollato con conferma: PF 1,14, +0,079R,
2/3 asset, 5,7 trade/mese, 2021-12→2023). C3 +0,016R, C1 0,000R, C5 −0,011R, C0 −0,027R, C2 −0,024R, C7 −0,058R, C4 −0,213R.
Esito già fissato: la famiglia C NON passa. Il fuori campione si calcola per tutte solo per trasparenza; C6 riceve placebo,
vicini e senza-miglior-trade a titolo informativo (non può essere promossa).
