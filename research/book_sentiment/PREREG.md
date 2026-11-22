# Preregistrazione · indicatore di sentiment da order book e liquidazioni (22/11/2026)

Scritta e committata DA SOLA prima di calcolare qualsiasi rendimento. Finora sono stati eseguiti solo `bs_data.py` (caricamento)
e `bs_conteggi.py` (conteggi di osservazioni ed eventi, `conteggi.txt`): i prezzi a 1 minuto sono stati usati soltanto per stabilire
se un muro è stato toccato FRA due foto (definizione dell'evento), mai per rendimenti successivi.
Conoscenza pregressa da dichiarare: research/book_liq (stesso registro, stesso periodo) ha già misurato lo squilibrio ±1% come
correlazione di rango (1h ρ +0,14, p 0,031; 4h e 24h nulli). Le celle su I qui sotto NON sono quindi cieche: valgono come
ri-lettura con la statistica del segno, non come prova indipendente. Tutto il resto (L, S, regola, archivio) è cieco.

## Specifica dell'indicatore (fissa, decisa dalla regia; nessuna ottimizzazione)
- I = (bid − ask)/(bid + ask) in dollari entro ±1% dal prezzo medio: colonna `imb_1` di data/orderbook.csv (profondità ±1% esatta,
  book aggregato di Coinbase, Kraken, OKX perp e spot, Binance spot).
- L = (liquidazioni short − liquidazioni long)/(somma) in dollari nella finestra precedente; 0 senza liquidazioni.
- S = 0,5·I + 0,5·L; S > +0,2 "pressione al rialzo", S < −0,2 "pressione al ribasso", altrimenti neutro.

## Dati (inventario completo in conteggi.txt)
**Insieme A · registro** (identico a ciò che andrà in pagina): 275 foto del book dal 07/11 08:53 al 22/11 13:02 UTC (16 giorni
di calendario; ~8 al giorno fino al 13/11, orarie dal 14/11). L dagli eventi reali registrati con orario al millisecondo, quindi
finestra di **30 minuti prima della foto, come in pagina** (non serve ripiegare sull'ora): OKX, Gate, dYdX, Deribit, Kraken,
Lighter dal 10–11/11 (data/liq_events); prima solo OKX da data/liquidations.csv (ultimi 100 eventi per giro, incompleto). Mancano
Binance, Bybit e Hyperliquid: meno del 10% del mercato. Prezzo: candele 1 minuto BTCUSDT spot Binance; prezzo a t = apertura
della prima candela che inizia dopo la foto; rendimento a h = apertura h ore dopo.
**Insieme B · archivio (solo L)**: liquidazioni reali Binance COIN-M BTCUSD_PERP di data.binance.vision, 2023-06-25 → 2024-10-14
(472 giorni, 11.472 ore, 53.398 eventi, ~950 M$ in tutto: mercato piccolo, evento mediano 1.700 $). Unico storico lungo di
liquidazioni reali gratuito (l'archivio USDT-M non esiste). L = ora precedente [H−1, H); decisione e prezzo all'apertura dell'ora H
(data/spot_1h.csv). Il book storico non esiste: in B si pone I = 0, quindi S = 0,5·L (S > 0,2 ⇔ L > 0,4).
**Non testabile per mancanza di dati**: book prima del 07/11/2026; liquidazioni Binance/Bybit; ETH e altri asset (nessun registro:
"stessi parametri su tutti gli asset" non applicabile); tabella standard 10.000 $ dal 01/01/2021 (i dati non esistono: si riportano
W3.1 e buy & hold nella stessa finestra solo come contesto).

Osservazioni dai soli conteggi (senza rendimenti), che condizionano la lettura:
- S è quasi solo L: segno di S = segno di L in 253 foto su 275; L è bimodale (quartili −0,995 / +0,971; in 90 foto su 275 un solo
  lato), I supera ±0,2 solo in 23 foto. Correlazione I–L −0,42. S cambia stato 168 volte in 275 foto (autocorrelazione −0,07).
- Stati di S in A: rialzo 106, ribasso 132, neutro 37. In B: rialzo 2.830, ribasso 3.862, neutro 4.780 (4.410 ore senza liquidazioni).
- Osservazioni indipendenti in A: 16 giorni, ~90 blocchi di 4 ore, 15 finestre di 24 ore non sovrapposte.

## Domanda 1 · il segno predice il rendimento? (12 test di conferma)
Statistica unica: **Δ = rendimento medio dopo segno positivo − rendimento medio dopo segno negativo** (valori nulli esclusi),
in punti percentuali, per orizzonte h = 1, 4, 24 ore. Usare la differenza fra stati, non il rendimento "firmato", toglie la deriva
del periodo (A è un solo regime ribassista 76k → 61k).
- A: X ∈ {S, I, L} × h ∈ {1, 4, 24} = 9 test (i 3 su I non ciechi, vedi sopra).
- B: L × h ∈ {1, 4, 24} = 3 test.
p a due code da **placebo a blocchi**: spostamento circolare del segnale rispetto ai rendimenti (A: scarto fra 24 e N−24 foto,
5.000 ripetizioni; B: fra 48 e N−48 ore, 2.000), che conserva l'autocorrelazione di segnale e rendimenti sovrapposti.
IC 95% da bootstrap a blocchi (A: giorni di calendario; B: settimane). Due metà temporali: A 07–14/11 (85 foto) e 15–22/11 (190);
B fino al / dal 19/02/2024 (5.736 ore ciascuna).

## Domanda 2 · la regola rende dopo i costi? (2 test di conferma)
Regola: a ogni osservazione posizione = +1 se S > +0,2, −1 se S < −0,2, 0 altrimenti; eseguita al prezzo t definito sopra, tenuta
fino all'osservazione successiva (A: foto successiva, qualunque sia l'intervallo; B: ora successiva). 10.000 $ a 1x, capitalizzazione
composta. Costi: commissione 0,05% + slippage 0,05% **per lato** = 0,10% per lato, 0,20% andata e ritorno, 0,20% per un rovesciamento
(lettura prudente di "0,05% per lato + 0,05% slippage"; sensibilità a 0,075% per lato). Funding non incluso (posizioni di ore).
Si riportano: capitale finale, rendimento, max drawdown giornaliero, trade, win rate, MAR (in A su 15 giorni è solo formale), lordo
e netto, buy & hold e W3.1 nella stessa finestra.
- RA: regola su A. RB: regola su B (S = 0,5·L).
Test: rendimento LORDO totale della regola contro la stessa regola con il segnale spostato a blocchi (stessa frequenza di trade),
p a una coda. **"Rende" solo se**: capitale netto finale > 10.000 $ in entrambe le metà E p corretto < 0,05.
Varianti di robustezza (≤ 8, non di conferma, mai usate per scegliere): V1 = regola; V2/V3 soglia ±0,1 / ±0,3; V4 solo I;
V5 solo L; V6 finestra L di 60 minuti (solo A); V7 regola rovesciata (diagnostica: se perde anche lei, sono i costi);
V8 decisione ogni 4 ore. In più: senza il trade migliore; A solo dal 11/11 (liquidazioni multi-fonte).

## Test multipli
Famiglia di conferma = 12 + 2 = **14 test, correzione di Holm** (α 0,05). Esiti per cella, fissati ora:
- **"predice"**: p di Holm < 0,05 e stesso segno di Δ nelle due metà;
- **"indizio"**: p grezzo < 0,05 e stesso segno nelle due metà, ma non regge Holm (non si mostra come segnale);
- altrimenti si guarda la potenza (sotto): **"nessun effetto utile"** se l'effetto minimo rilevabile è ≤ dell'effetto di
  riferimento, **"non dimostrabile con questi dati"** se è più grande. Mai "non funziona" con potenza insufficiente.

## Potenza (calcolata dallo stesso placebo, prima di leggere Δ)
Errore standard sotto l'ipotesi nulla SE₀ = deviazione standard di Δ nelle ripetizioni del placebo a blocchi (incorpora
autocorrelazione e sovrapposizione). Effetto minimo rilevabile con potenza 80%: MDE = 2,80·SE₀ (α 0,05 a due code) e 3,75·SE₀
(al primo passo di Holm, α 0,05/14). Effetti di riferimento, fissati ora:
- **utile**: Δ = 0,40% (una regola long/short incassa circa Δ/2 per operazione contro 0,20% di costi);
- **plausibile**: Δ = 0,10% (metà dello scarto Q5 − Q1 di +0,23% a 1 ora visto in book_liq; la letteratura sullo squilibrio del
  book trova effetti a secondi/minuti, non a ore).
Settimane di registro necessarie = settimane attuali × (MDE / effetto)², per 1h, 4h e 24h, con foto orarie.

## Controlli non di conferma (dichiarati come tali)
Etichette di S a ±0,2 (rialzo contro ribasso); Spearman e quota di segni corretti; L solo con ≥ 100.000 $ nella finestra; finestra
60 minuti in A; legame con il passato: correlazione di I, L, S con il rendimento dell'ora e delle 24 ore PRECEDENTI e confronto con
il "segnale" banale segno del rendimento dell'ora precedente (L è meccanicamente legato alla mossa appena avvenuta: se L predice
quanto il momentum di un'ora, non aggiunge nulla; lezione 81); coefficiente di segno(L) in una regressione con il rendimento
dell'ora precedente.

## Domanda 3 · dopo una cascata rimbalzo o prosecuzione? NON si rifà
Già testato: research/liq_fasce R4/R5 (proxy 345 cascate dal 2021 e 31 + 53 cascate reali COIN-M 2023-06 → 2024-10: né
continuazione né rimbalzo battono il caso dopo i costi; lezione 92) e research/liq_squeeze (lezione 93). Nel registro attuale le
ore con ≥ 10 M$ e un lato ≥ 75% sono 17 long (9 episodi) e 4 short (3 episodi): troppo poche per aggiungere qualcosa. Si cita l'esito.

## Domanda 4 · muri ritirati: NON testabile, solo conteggi
data/book_walls.csv (muri per exchange) ha una sola foto: zero coppie. data/orderbook.csv registra un solo muro per lato sul book
aggregato, con foto orarie: con la definizione della pagina (scomparsa ≥ 70% senza che il prezzo lo tocchi) gli eventi sono **0**
su 454 muri osservati; con una definizione larga (muro non toccato, ancora nella finestra, nuovo massimo altrove e più piccolo)
46 (22 bid, 24 ask; 14 con muro ≥ 3×), e a un'ora di distanza un muro che cambia è normale ricambio di ordini, non ritiro.
Nessun test di conferma. Solo descrittivo sui 46 eventi larghi (rendimento a 1h e 4h dopo ritiro bid e ask), dichiarato privo
di valore probatorio, più il calcolo di quanti eventi servono.

## Cosa NON si fa
Nessuna modifica alla specifica (pesi, soglie, profondità) in base ai risultati; nessuna regola per W3.1; nessuna modifica fuori
da research/book_sentiment/. Ogni deviazione si scrive nel README sotto "Deviazioni", con il motivo.
