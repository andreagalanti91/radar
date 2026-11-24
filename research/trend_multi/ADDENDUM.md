# trend_multi · ADDENDUM U2 — universo negoziabile con perpetui su OKX/Bitget (23/11/2026)

Scritto e committato da solo PRIMA di scaricare i dati di U2 e di calcolare qualsiasi rendimento di U2. A questo punto dello
studio ETF (PREREG 3ca3620) è stato scaricato solo parte dei prezzi; nessun rendimento calcolato. Motivo: nuovo vincolo
dell'utente ("niente ETF/ETP, solo azioni; opererei con Bitget o OKX"). Lo studio ETF resta il riferimento "da manuale";
la risposta operativa riguarda U2. Stesse regole di trend, dimensione, ribilanciamento, periodi e metriche del PREREG.

## Universo U2 primario (26 mercati), fissato ora
- **Azioni (20)**: componenti del Dow Jones al 01/01/2000 (insieme definito 16 anni prima del giudizio) che oggi hanno un
  perpetuo USDT su OKX (instCategory 3) o Bitget (isRwa = YES), elenchi scaricati il 23/11/2026 (data/u2/):
  BA CAT C GE HD HPQ IBM INTC JNJ JPM KO MCD MO MRK MSFT PG RTX T WMT XOM. Esclusi perché senza perpetuo: AA, AXP, DD, DIS, HON,
  IP, MMM; senza storia continua: EK, GM, SBC. Bias residuo dichiarato: "ha un perpetuo oggi" e "esiste ancora" sono noti a posteriori.
  Storia: sottostante rettificato per split e dividendi (research/multi_asset/data/dow2000 e MSFT, Yahoo, taglio 20/11/2026).
- **Materie prime (6)**: oro, argento, petrolio, gas naturale, rame, platino (perpetui XAU, XAG, CL/BZ, NG, XCU, XPT).
  Storia primaria = ETF che detiene il metallo o rinnova i future, perché contiene il costo di rinnovo che il prezzo del
  primo future nasconde: GLD, SLV, USO, UNG, CPER, PPLT (solo come serie storica: l'utente non li comprerebbe). Controllo:
  primo future continuo di Yahoo (GC=F, SI=F, BZ=F al posto di CL=F per il prezzo negativo dell'aprile 2020, NG=F, HG=F, PL=F),
  dichiarato ottimistico sul gas. Un mercato entra con 273 sedute di storia.
- **U2 "elenco di oggi" (solo descrittivo, OTTIMISTICO)**: tutte le azioni singole con perpetuo sia su OKX (categoria 3) sia su
  Bitget (isRwa) che Yahoo classifica come azione (instrumentType EQUITY) con lo stesso ticker, più le 6 materie prime. Sono i
  titoli di moda scelti a posteriori: nessun criterio, serve solo a misurare quanto il bias gonfia il risultato.

## Costi e ipotesi dei perpetui (il backtest usa il sottostante: i perpetui azionari hanno pochi mesi di storia)
- Commissione 0,05% + slippage 0,05% per lato (0,10%), come nel PREREG.
- **Funding non noto** per i perpetui azionari: ipotesi primaria 5% annuo pagato sul nozionale long; short: nessun incasso e 1%
  annuo di costo. Sensibilità: funding long 0% e 10%.
- Collaterale (USDT) non remunerato: liquidità a 0% (primaria); sensibilità con T-bill su tutto il capitale non impegnato.
- Nessuna leva: Σ|w| ≤ 1. Il segnale resta l'eccesso sul T-bill a 1/3/12 mesi.

## Candidate, riferimenti, criteri (giudizio 01/01/2016 → 20/11/2026, una sola volta)
Candidate: U2-V1 (long/flat) e U2-V2 (long/short), parametri identici a V1/V2. Con le due del PREREG le candidate sono 4:
soglia del bootstrap p < 0,0125. Varianti di robustezza: le stesse V3–V6, V8 e controlli del PREREG.
Riferimenti: equipesato di U2 tenuto con perpetui (stesso funding 5% sui long, ribilanciato ogni mese) e lo stesso senza
funding; S&P 500 (SPY con dividendi, senza funding: riferimento teorico); liquidità (T-bill e 0%).
Criteri (tutti, per candidata):
1. CAGR/DD > equipesato di U2 con lo stesso funding e > S&P 500;
2. max DD ≥ −25%;
3. rendimento positivo in entrambe le metà (2016–20, 2021–26) e CAGR > CAGR del T-bill (altrimenti non conviene rischiare);
4. eccesso giornaliero sul T-bill > 0, bootstrap a blocchi come nel PREREG, p < 0,0125.
Verdetto come nel PREREG ("funziona" / "non funziona" / "non dimostrabile"). Robustezza per chi passa 1–4: criterio 1 e CAGR > 0
ancora veri con funding 10%, con costi doppi, con ribilanciamento settimanale, con i future al posto degli ETF-serie, in almeno
2 su 3 segnali alternativi, e senza le materie prime / senza le azioni (almeno uno dei due).
Controllo aggiuntivo descrittivo: rischio uguale per classe (metà azioni, metà materie prime) invece che per mercato.

## README
Verdetto separato ETF (riferimento) e U2 (operativo); operazioni l'anno; posizioni di oggi in U2; sezione "prima di operare"
con ciò che non è verificato: funding reale, orari e liquidità dei perpetui azionari, rischio di controparte, restrizioni
sui derivati per residenti UE/Italia.
