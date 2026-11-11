# Analisi tecnica settimanale / mensile su BTC · media 200 giorni × MACD (10–11/11/2026)

Richiesta: studiare una strategia settimanale/mensile con EMA, SMA, S/R, volume, liquidazioni, order book; correlazione fra
EMA/SMA 200 giorni e MACD. Regole e soglie scritte in `PREREG.md` prima dei risultati. Dati: Bitstamp 2011-09 → Binance →
repo, fino al 09/11/2026. Dal 01/01/2021, 10.000 $ a 1x, costi di `radar/weekly.py`.

**Verdetto: nessuna regola da aggiungere a W2 (tutte respinte). T1 e T4m solo su carta come termine di paragone.
In dashboard vale la pena mostrare come contesto: SMA200g e sua pendenza, Mayer multiple, stato MACD, media 200 settimane.**

## Limiti dichiarati
- Corsa unica, controlli ridotti su indicazione del coordinatore: NON sono stati fatti i parametri vicini previsti in PREREG;
  il placebo solo sulle 3 regole autonome che superavano il buy & hold. 14 configurazioni provate: una "vincente" per caso è attesa.
- MAR = rendimento totale / |DD| come nel tool (non confrontabile fra periodi di durata diversa).
- Pre-2021 delle regole sopra W2 = 2018–20 con flusso proxy (CVD spot), funding 0 prima del 2020.
- Non ritestati (già esclusi, lezioni 68, 72, 75–77, 81): S/R, volume profile, liquidazioni. **Order book: storico solo dal
  07/11/2026, non backtestabile** → resta nota di monitoraggio; rivalutare con ≥ 6–12 mesi di dati.

## 1 · Descrittiva (750 settimane, 07/2012 → 11/2026; dettagli in `descrittiva.txt`, `desc_*.csv`)

**Accordo.** Prezzo sopra/sotto MA200g e MACD sopra/sotto ZERO dicono quasi la stessa cosa; MACD vs SEGNALE è un'informazione diversa.

| Confronto con "prezzo > SMA200g" | settimane concordi | phi |
|---|---|---|
| MACD 8/21/5 > 0 | 93,9% | 0,87 |
| MACD 12/26/9 > 0 | 86,5% | 0,71 |
| MACD 12/26/9 > segnale | 73,2% | 0,44 |
| MACD 8/21/5 > segnale | 62,9% | 0,23 |

EMA200g al posto di SMA200g: stessi numeri (±2 punti). Distanza dalla SMA200g e MACD/prezzo: Spearman 0,87–0,95 (per
costruzione: sono entrambi differenze di medie). Stabile pre-2021 e dal 2021.

**Chi gira prima** (9 massimi seguiti da −30%, 8 minimi seguiti da +50%; settimane mediane dalla svolta, prezzo a quel punto):

| Indicatore | massimi: sett. | prezzo dal top | minimi: sett. | prezzo dal minimo |
|---|---|---|---|---|
| MACD 12/26/9 sotto/sopra segnale | 3 | −18% | 6,5 | +45% |
| MACD 8/21/5 sotto/sopra segnale | 5 | −15% | 5,5 | +38% |
| Prezzo sotto/sopra SMA200g | 7 | −29% | 7,5 | +38% |
| MACD 12/26/9 sotto/sopra zero | 16 | −36% | 6,5 | +43% |
| Death/golden cross 50/200g | 11 | −34% | 10,5 | +41% |
| Pendenza SMA200g cambia segno | 24 | −28% | −22 (inutile ai minimi) | — |

Ai massimi il MACD (segnale) gira prima della SMA200g in 9 svolte su 9, anticipo mediano 6 settimane; ai minimi nessun
ordine (3 su 8). Tutti arrivano tardi: il segnale più rapido costa già −15/−18% dal top.

**Rendimenti futuri nei 4 stati** (SMA200g × MACD 12/26/9 vs segnale; media a 4 settimane, p da permutazione):

| Stato | n | 4 sett. tutto | pre-2021 | dal 2021 | 26 sett. dal 2021 |
|---|---|---|---|---|---|
| sopra · MACD > segnale | 351 | +16,0% (p 0,01) | +21,8% (p 0,03) | +5,7% (p 0,02) | +8,6% |
| sopra · MACD < segnale | 117 | +1,6% | +6,1% | −5,9% (p 0,01) | +14,8% |
| sotto · MACD > segnale | 84 | +0,2% | −0,7% | +1,1% | +28,5% |
| sotto · MACD < segnale | 198 | +2,7% | +3,1% | +2,3% | +12,2% |
| tutte | 750 | +8,5% | +12,6% | +2,3% | +12,9% |

L'unico fatto con lo stesso segno prima e dopo il 2021: "sopra la SMA200g con MACD sopra il segnale" è lo stato migliore a
4 settimane. A 12 e 26 settimane non c'è nulla di significativo, e dal 2021 la SMA200g da sola non separa più i rendimenti
(sopra +4,6% vs sotto +9,2% a 12 settimane). Con MACD vs zero: nessuno stato significativo in entrambi i periodi.

**Mayer multiple** (chiusura / SMA200g; oggi 1,02):

| Fascia | n | media 12 sett. | % positivi 12 sett. | mediana 26 sett. |
|---|---|---|---|---|
| < 0,8 | 120 | +7,1% | 48% | +1,9% |
| 0,8–1 | 162 | +7,2% | 49% | −0,3% |
| 1–1,5 | 332 | +50,2% | 69% | +45,4% |
| 1,5–2,4 | 108 | +56,0% | 63% | +50,3% |
| > 2,4 | 28 | +3,2% | 32% | −8,3% |

Sopra 2,4 = surriscaldamento reale (mediana a 12 settimane −21%), ma solo 28 settimane in 8 episodi di 3 cicli (2013, 12/2017–
01/2018, 01–02/2021) e mai più dal 02/2021: p non significativo. Sotto 0,8 NON è un segnale d'acquisto affidabile.

**Altro.** Pendenza SMA200g: in salita +45,9% a 12 settimane contro +4,6% in discesa sull'intero campione, ma p 0,26 e dal
2021 la differenza si riduce (+9,9% vs +0,2%). Media 200 settimane: sotto solo 54 settimane (7%), poi 92% positivi a 26
settimane (+50% mediano), ma sono 3–4 episodi indipendenti. Golden/death cross 50/200g (12 + 12 eventi): inutili — dopo un
death cross mediana +13,7% a 182 giorni, dopo un golden cross +35,8% contro +30,4% di un giorno qualunque; golden cross
positivi fino all'incrocio opposto solo 6 su 12.

## 2 · Regole (`regole.csv`, `regole.txt`)

| Regola | Finale $ | Rend. | DD | Trade | WR | MAR | In mercato | 2021–23 | 2024→ | Pre-2021 (rend / DD) |
|---|---|---|---|---|---|---|---|---|---|---|
| **W2 + MACD com'è** | 118.628 | +1.086% | −22,7% | 14 | 93% | 47,9 | 61% | +406% | +134% | +117% / −48% (2018–20) |
| Buy & hold | 25.099 | +151% | −76,7% | 1 | — | 2,0 | 100% | +44% | +74% | +116% / −81% (2018–20); +3.739% / −83% (2014–20) |
| T1 SMA200g + MACD>segnale, long | 39.155 | +292% | −36,4% | 9 | 67% | 8,0 | 42% | +90% | +106% | +4.884% / −59% |
| T1 long/short | 16.717 | +67% | −59,4% | 22 | 41% | 1,1 | 72% | +38% | +22% | +1.307% / −83% |
| T2 EMA200g + MACD>segnale, long | 34.720 | +247% | −41,5% | 10 | 50% | 6,0 | 42% | +77% | +96% | +5.772% / −59% |
| T2 long/short | 26.652 | +167% | −47,3% | 23 | 35% | 3,5 | 70% | +78% | +50% | +1.315% / −83% |
| T3 pendenza SMA200g + MACD>0, long | 11.679 | +17% | −74,0% | 6 | 50% | 0,2 | 61% | −16% | +39% | +2.498% / −71% |
| T3 long/short | 19.490 | +95% | −77,8% | 8 | 63% | 1,2 | 90% | +20% | +62% | +169% / −97% |
| T4 Faber 10 mesi, long | 50.735 | +407% | −53,2% | 3 | 67% | 7,7 | 67% | +154% | +100% | +3.084% / −72% |
| T4 long/short | 88.896 | +789% | −53,2% | 5 | 80% | 14,8 | 99% | +288% | +129% | +1.109% / −83% |
| T4m Faber + MACD>segnale, long | 38.662 | +287% | −36,4% | 8 | 63% | 7,9 | 40% | +94% | +100% | +3.555% / −58% |
| T4m long/short | 59.389 | +494% | −36,4% | 12 | 67% | 13,6 | 58% | +177% | +114% | +450% / −88% |
| W2 + T5 uscita Mayer > 2,4 | 87.156 | +772% | −22,7% | 13 | 92% | 34,0 | 60% | +272% | +134% | +123% / −47% |
| W2 + T6 volume > media 20 sett. | 50.442 | +404% | −37,8% | 13 | 85% | 10,7 | 49% | +287% | +30% | +78% / −48% |
| W2 + T7a MACD mensile > 0 | 108.476 | +985% | −22,7% | 12 | 100% | 43,4 | 48% | +344% | +144% | +16% / −48% |
| W2 + T7b RSI mensile > 50 | 79.360 | +694% | −25,1% | 13 | 92% | 27,6 | 53% | +225% | +144% | +117% / −48% |
| W2 + T8 SMA200g + pendenza | 63.098 | +531% | −22,7% | 12 | 83% | 23,4 | 52% | +166% | +137% | +85% / −44% |

Pre-2021 = 2014–20 per T1–T4, 2018–20 per W2 e T5–T8. Nessuna regola batte W2 dal 2021 in capitale finale o MAR.

## 3 · I filtri avrebbero evitato le perdite di W2? (`trade_w2_diagnosi.csv`)

| Filtro | Trade W2 cambiati dal 2021 | Cosa toglie | 2018–20 | Long 01/2018 (−41%) | Long 08→11/2026 (−4%) |
|---|---|---|---|---|---|
| T5 Mayer | 2 | +15% e parte del +77% (01–02/2021) | 1 | rinviato di 1 settimana: −40% | resta |
| T6 volume | 4 | rinvia/taglia 4 vincenti, aggiunge un −15% | 1 | resta | resta |
| T7a MACD mensile | 2 | il −4% e un +14% | toglie +51% e +24% | resta | evitato |
| T7b RSI mensile | 3 | il −4%; rinvia +14% (→ −15%) e +40% (→ +20%) | 0 | resta | evitato |
| T8 SMA200g + pendenza | 5 | il −4%; rinvia 3 vincenti (2 diventano perdite) | 4 | resta | evitato |

- **Nessun filtro 200 giorni o mensile blocca il long di gennaio 2018**: al segnale del 07/01/2018 prezzo sopra la SMA200g
  in salita, MACD mensile e RSI mensile positivi, volume sopra la media. Solo il Mayer (2,47) lo ferma, ma il rientro scatta
  la settimana dopo (Mayer 1,94 < 2,0) e perde −40%. Il rischio "long vicino a un top" resta scoperto.
- Il −4% del 2026 è evitato da T7a, T7b e T8, ma ognuno paga con vincenti: T7a cambia solo 2 trade dal 2021 (senza potenza)
  e nel 2018–20 scende da +117% a +16%; T7b e T8 chiudono a 79k e 63k contro 118,6k.
- W2 richiede già chiusura sopra la SMA 40 settimane (= 280 giorni) ed EMA20w in salita: la media 200 giorni è quasi un doppione.

## 4 · Verdetto per regola
- **T5, T6, T7a, T7b, T8 (sopra W2): respinte.** Nessuna ha MAR ≥ W2 in entrambi i sottoperiodi; T5 e T7a cambiano meno di 3 trade.
- **T3 e tutte le versioni long/short: respinte** (DD −47/−78%; nel 2014–20 gli short portano il DD a −83/−97%). Conferma la lezione 80.
- **T4 Faber puro: respinto** (3 trade dal 2021, DD −53%).
- **T1 long e T4m long: su carta** secondo le soglie preregistrate (MAR sopra il buy & hold in tutti e 3 i periodi, DD −36,4%,
  placebo p 0,047 e 0,037 — `placebo.txt`). Ma: finale 39k contro 118,6k di W2, DD peggiore, p al limite con 14 prove, vicini
  non testati. Servono come termine di paragone "analisi tecnica classica", non come seconda strategia.
- **T2 (EMA200g): respinta** per DD −41,5% (soglia −40%); di fatto equivalente a T1.

## 5 · Cosa mostrare in dashboard (contesto, non segnale)
1. SMA200g con pendenza a 28 giorni e posizione del prezzo (oggi: 74.851 sopra SMA200g 73.224, sotto EMA200g 76.512).
2. Mayer multiple con fasce (oggi 1,02; > 2,4 = surriscaldamento storico, raro).
3. Stato combinato "sopra SMA200g + MACD settimanale sopra il segnale" (l'unico stato con rendimento a 4 settimane sopra la
   media in entrambi i periodi), con la nota che ai massimi il MACD gira circa 6 settimane prima della SMA200g.
4. Media 200 settimane (oggi 67.760) come livello di fondo ciclo.
Non mostrare come segnale: golden/death cross, Mayer < 0,8.

## Lezione proposta per RESEARCH.md
> 83. Media 200 giorni × MACD settimanale (750 settimane dal 2012, 14 configurazioni): prezzo vs MA200g e MACD vs zero sono
> la stessa informazione (concordi 87–94%); ai massimi il MACD-segnale gira ~6 settimane prima della MA200g (9 su 9) ma a
> −15/−18% dal top. Nessun filtro 200g, mensile (MACD, RSI, Faber), Mayer o volume migliora W2: tolgono il −4% del 2026 solo
> tagliando vincenti, e nessuno blocca il long di gennaio 2018 (−41%). SMA200g, Mayer e stato MACD vanno in dashboard come
> contesto. Golden/death cross inutili. Order book non backtestabile prima di metà 2027.

## File
`PREREG.md` · `lib.py` (dati, indicatori, motori) · `descrittiva.py` → `descrittiva.txt`, `desc_*.csv` · `regole.py` →
`regole.csv`, `regole.txt`, `trade_w2_diagnosi.csv` · `placebo.py` → `placebo.txt` · `fetch.py` → `data/bitstamp_1d_2011_2013.csv`
