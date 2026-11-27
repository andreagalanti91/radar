# PREREG · SOL con W3.2 · varianti V1–V3 · 27/11/2026

Scritto DOPO il rapporto descrittivo A (`rapporto_a.py`, replica di `w32_asset2` Q7) e PRIMA di qualsiasi calcolo di V1–V3.
**Va committato da solo, prima di eseguire lo script delle varianti** (errori operativi: l'ordine deve essere provabile con git).
W3.2, `radar/weekly.py`, i segnali, gli stop e i capitali di BTC ed ETH non cambiano. Nessuna modifica al tool.

## Già noto e dichiarato (rischio di adattamento)
Le varianti sono scelte dopo aver visto il risultato base di SOL: 80.661 $ dal 11/01/2021 al 24/11/2026 (rischio 25%), DD −39,8%,
22 chiuse + 1 aperta, WR chiuse 45% (48% contando l'aperta), long 15 (6 vinti), short 7 (4 vinti) + short aperto, dal 2024 −10%;
somme per anno e lato in `w32_asset2/out_q7.txt` (i long del 2025 perdono 42 punti); vicini trailing 2,0/3,0: CAGR/DD 0,36/1,16;
cancello BTC (Q4): 52.037 $, DD −40,1%; solo prezzo 242.595 $ con DD −58,3%. Lezioni 74, 87, 110, 111, 123: il vantaggio di W3.2
non si trasferisce alle altcoin. Per questo **le soglie sono più severe di `w32_asset2`** (segnate con ★).

## Dati, motore, periodi (fissati)
- Motore `radar.weekly.simulate` invariato tramite `research/w32_asset2/lib.py` (`csim`, `omet`, `bh`, `placebo`, `port`), dati
  congelati `research/w32_asset2/crypto/data`, costi del motore e funding reale. Fine dati **24/11/2026**.
- Inizio **2021-01-11** per SOL (convenzione `w32_asset2`, lunedì dopo la prima domenica calcolabile). L'avvio alternativo
  2021-01-10 (84.298 $ nel base) è solo una nota, non entra nei verdetti.
- **IS 2021-01-11 → 2022-12-31, OOS 2023-01-01 → 2026-11-24.** Scelta: è la divisione del PREREG di `w32_asset2` (nessun nuovo grado
  di libertà scelto dopo aver visto SOL); l'IS contiene un toro (2021) e un orso (2022); l'OOS (3,9 anni) contiene la fase debole
  2024–26 e quindi è il test duro. Il 2023-06-30 è scartato perché sarebbe una scelta nuova fatta sapendo dove cadono le perdite del
  primo semestre 2023. In più, per il metodo, si riportano 2021–2023 e 2024-01-01 → fine (★ il secondo entra nei criteri).
- Ogni periodo riparte da 10.000 $ e da flat. Posizione aperta valutata all'ultima chiusura (con la commissione d'uscita).

## Varianti (6 al massimo; nessun'altra dopo i risultati)
- **V1 · solo long**: i segnali short di SOL sono ignorati (da flat su un segnale short si resta flat); tutto il resto invariato.
  Realizzazione: `csim(..., gate=+1 su tutte le domeniche)`.
- **V2 · cancello ETH**: ingresso su SOL solo se alla stessa domenica W3.2 su ETH è in posizione nello stesso verso o vi entra quel
  giorno (segnale ETH della stessa domenica); uscite proprie di SOL. ETH = W3.2 dal 2020-06-01 (completa da), parametri invariati,
  definizione identica a `w32_asset2/q4.py` (in posizione alla domenica d se entrata ≤ d < uscita) con ETH al posto di BTC.
- **V3a / V3b · portafoglio**: conto A = BTC 30.000 $ + ETH 30.000 $ (W3.2 a 25%, conti separati, da flat il 2021-01-11). Conto B =
  A + SOL W3.2 base su conto separato da 10.000 $ a rischio **10% (V3a)** e **25% (V3b)**. Conto unico = somma dei dollari dei tre
  conti (pesi 30/30/10, non capitali uguali).
- **V3c / V3d** (solo se V1 o V2 risulta "operabile"): come V3a/V3b con la variante operabile al posto del base; se lo sono entrambe,
  quella con il CAGR/DD più alto sul periodo intero.
- V1 e V2 si giudicano a **rischio 25%** (come BTC ed ETH); 10% e 15% solo descrittivi.

## Criteri V1/V2 "operabile" (periodo intero, rischio 25%)
1. CAGR/DD > B&H SOL dello stesso periodo **e** ★ ≥ CAGR/DD di W3.2 ETH nello stesso periodo (0,96: l'asset marginale già in uso).
2. DD giornaliero ≥ −35%.
3. ★ Win rate ≥ 60% sulle **sole operazioni chiuse** (l'aperta non conta).
4. Rendimento positivo in IS e in OOS e ★ dal 2024-01-01.
5. ≥ 8 operazioni (chiuse + aperta).
**Conferma**: senza il trade migliore finale > 10.000 $; ★ vicini trailing 2,0 **e** 3,0 ATRw entrambi con CAGR/DD > B&H (non metà).
**Placebo**: `lib.placebo` (= `w32_multi/placebo.py`, 2.000 prove, seme 7), periodo intero. ★ **Holm α = 0,05 con m = 6** (tutte le
varianti dichiarate, anche quelle senza placebo): p di V1 e V2 ordinati, soglie 0,05/6 = 0,0083 e 0,05/5 = 0,010.
"Operabile" = 1–5 + conferma + placebo significativo dopo Holm.

## Criteri V3 "migliora" (Q6 di `w32_asset2`, più severo)
Conto B contro conto A: CAGR/DD del conto unico più alto **e** DD non peggiore di 3 punti, ★ sul periodo intero **e** separatamente
in IS e OOS, ★ e ancora vero togliendo il trade migliore di SOL (rendimenti giornalieri del conto SOL posti a zero fra entrata e
uscita di quel trade). Si riportano anche: finale, CAGR, DD, correlazione dei rendimenti giornalieri (conto SOL contro conto A; tutti
i giorni e solo i giorni con SOL in posizione) e settimanale, operazioni aggiunte l'anno, quota delle settimane in posizione su SOL
con BTC/ETH nello stesso verso, opposto o flat.

## Verdetti (fissati ora)
- **"SOL operabile con W3.2"**: V1 o V2 operabile **e** V3c/V3d migliora → proposta all'utente (non applicata).
- **"Solo diversificatore"**: nessuna fra V1 e V2 operabile, ma V3a o V3b migliora → SOL resta fuori dai criteri per asset; si presenta
  all'utente come scelta di rischio, al più a rischio 10% su conto separato, con i limiti scritti.
- **"Non operabile"**: altrimenti. Nessun secondo ciclo di varianti su SOL senza un'ipotesi nuova motivata da fuori di questi dati.

## Uscite previste
`varianti.py` → `out_v.txt`, `risultati_v.csv`, `trades_v.csv`; sezione "Fase 2" del `README.md`; revisione critica separata.
