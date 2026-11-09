# Famiglia D · Uscite ("la costante" TP1/TP2/uscita totale) e leva — preregistrazione (09/11/2026, PRIMA dei risultati)

**Fase ESPLORATIVA.** Nessun ingresso delle famiglie A–C ha passato i criteri. Si studiano le uscite sull'unico ingresso con un
vantaggio reale sul placebo: **A1 = Ichimoku TK cross 4h nel verso della nube** (tk 9, kj 26, sb 52; codice `A_trend/strategies_a.ichi`),
BTC/ETH/SOL perp, stessi parametri sui 3 asset. Anche se una politica superasse tutti i criteri, il risultato resta condizionato
alla scelta di A1 fatta dopo aver visto il fuori campione di A (rischio di selezione): al massimo "candidata per la carta".

Regole comuni: ../PIANO.md (costi 0,05% + slippage 0,02%/0,05% stop, funding reale, liquidazione isolata, ingresso all'apertura
successiva, una posizione per asset, capitale 10.000 $). Segnali con posizione aperta ignorati; nessuna uscita su segnale opposto.
Stop = multiplo di ATR Wilder 14 alla barra del segnale (uno stop in % "dimensionato con l'ATR" è la stessa cosa: stop% = k·ATR/prezzo).

## Politiche di uscita (8)
| id | stop | prese di profitto (frazioni della size iniziale) | pareggio | trailing | uscita a tempo |
|---|---|---|---|---|---|
| E1 REF | 1,5 ATR | 50% a +1,5R, 50% a +3R | dopo TP1 | — | 12 barre (2 giorni) |
| E2 L78 | 2 ATR | 100% a +3R | — | — | 48 barre (8 giorni) |
| E3 COST5/10 | 2 ATR | 50% a **+5%**, 50% a **+10%** del prezzo (esempio dell'utente) | dopo TP1 | — | 72 barre |
| E4 TP1+TRAIL | 2 ATR | 50% a +2R | dopo TP1 | 3 ATR dal massimo, solo dopo TP1 | 120 barre |
| E5 3-STEP | 2 ATR | 33% a +1R, 33% a +2R, 34% a +4R | dopo TP1 | — | 72 barre |
| E6 2R | 2 ATR | 100% a +2R | — | — | 72 barre |
| E7 CHAND | 2 ATR iniziale | nessun TP fisso | — | chandelier 3 ATR dal massimo (dal primo bar) | 180 barre (tetto) |
| E8 OI | la migliore fra E1–E7 in campione | idem | idem | idem | idem — più filtro OI in espansione: z180 della variazione OI a 24h (6 barre 4h) > +1 alla barra del segnale (come C3); dati dal 2021-12 |

**Ricerca della "costante" in % (risposta alla richiesta dell'utente, vicini di E3, non una variante in più):** stop 2 ATR, pareggio
dopo TP1, 72 barre, 50/50; TP1 ∈ {3, 4, 5, 6, 8}%, TP2 ∈ {6, 8, 10, 12, 15, 20}% con TP2 ≥ 1,5·TP1. Si sceglie la coppia con
aspettativa R più alta **in campione** (a parità entro 0,02R il MAR più alto) e si guarda il fuori campione una volta sola.

## Sizing
- Scelta e confronto delle politiche: sizing di riferimento della famiglia A, `Sizing(mode="risk", risk_pct=0.01, leverage=2,
  allocation="equal", max_exposure=3)`.
- Griglia leva (per E1, E3, la politica scelta e la costante scelta): rischio 0,5% / 1% / 1,5% a trade × leva massima 2x / 3x / 5x,
  con `allocation="shared"` (nozionale per trade ≤ L × capitale, somma dei nozionali ≤ L × capitale, margine isolato a L ⇒ prezzo
  di liquidazione a ~1/L − 0,5% dall'ingresso). Più, per mostrare il rischio di liquidazione, "leva piena": `mode="fixed"`,
  nozionale = L × capitale/3 per asset (L × capitale in totale), L = 2/3/5. Si riportano DD, liquidazioni e distanza minima
  fra stop e prezzo di liquidazione.

## Scelta (solo 2021-01-01 → 2023-12-31; E8 dal 2021-12-01)
Ammesse: PF ≥ 1,1, aspettativa > 0, 2–12 trade/mese, max DD ≤ 25% in campione. Scelta: aspettativa R più alta (a parità entro
0,02R il MAR più alto). E8 = la scelta + filtro OI; E8 si confronta con la scelta sullo stesso periodo dal 2021-12.

## Giudizio (2024-01-01 → oggi, una volta, capitale fresco) — tutti i criteri del PIANO
1 PF ≥ 1,3 e ≥ +0,15R · 2 max DD giornaliero ≤ 20% · 3 positivo in campione e fuori, e ≥ 2/3 asset positivi fuori · 4 2–12
trade/mese · 5 placebo 500 giri (engine.placebo, seed 0, STESSE uscite, stop campionati dai trade reali) > 90° pct su exp_R e
rendimento · 6 vicini one-at-a-time ×0,8/×1,2 sui parametri d'uscita (stop, TP, tempo, trailing) e sul segnale (tk, kj):
mediana exp_R fuori campione > 0 · 7 PnL fuori campione senza il trade migliore > 0.
Placebo come controllo delle uscite: si riporta per ogni politica la mediana del placebo (ingressi casuali con le stesse uscite):
un'uscita non dovrebbe "creare" un vantaggio su ingressi casuali (atteso: mediana placebo ≤ 0R).
Confronti: buy & hold dal 01/01/2021 (1/3 BTC-ETH-SOL e solo BTC, 1x) e W2 + MACD (Memoria di RESEARCH.md).
