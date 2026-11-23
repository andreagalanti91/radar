# EMA e SMA su BTC a 4 ore, giornaliero e settimanale · atlante dei pattern e regole long/short · 23/11/2026

PREREG: commit `9a33184` (da solo, prima di ogni rendimento). Dati leggibili: [DATI.md](DATI.md).

## Verdetto
**Non esiste una regola di medie mobili che regga: nessuna modifica a W3.2.** La regola scelta dalla scoperta 2021–23 perde nel
giudizio 2024–26 e non regge nel 2018–20; l'esempio dell'utente (long sopra la SMA200 giornaliera, inversione short a 2 chiusure
4h sotto una media) porta 10.000 $ a 4.412 $ dal 2021 (DD −75%, 455 trade, WR 25%). Su 4.017 regole solo 14 (0,35%) sono positive,
meglio del buy & hold e con DD ≥ −35% in tutti e tre i periodi, e la migliore di queste (scelta a posteriori, quindi non valida)
fa 49.400 $ con DD −24% contro i 78.474 $ con DD −21% di W3.2.
**Una coerenza c'è, ma è una sola e già nota (Giro 9, lezione 83)**: le medie lente giornaliere usate per stare long o fuori
(long/flat) rendono circa come il buy & hold con metà del drawdown, in tutti e tre i periodi. Tutto il resto (short, inversione,
uscite a 4h, incroci, ritest, stiramenti, EMA contro SMA, 2–3 chiusure di conferma) non aggiunge nulla di stabile.

## Parte B · regole di entrata e uscita
Grammatica dichiarata prima: 6 regimi × 3 inneschi × 59 uscite × 4 lati = 4.017 regole, 87 famiglie (PREREG §3). Esecuzione
all'apertura della candela 4h successiva; long spot 0,1% + 0,1%, short perp 0,05% + 0,1% e funding reale (dal 2020; prima zero).

### Regola scelta, gemella, esempio dell'utente, W3.2, buy & hold (10.000 $ per periodo)
| | Conferma 2018–20 | Scoperta 2021–23 | Giudizio 2024–26 | Intero 2021–26 | Trade (WR) 2021–26 |
|---|---|---|---|---|---|
| **R1 scelta**: solo short, settimana sotto EMA20w, uscita alla chiusura 4h sopra la SMA200 4h | 10.231 $ (DD −42%) | 16.248 $ (−24%) | **8.584 $ (−41%)** | 13.947 $ (−51%) | 82 (20%) |
| R2 gemella (stessa uscita, regime SMA40w) | 9.142 $ (−37%) | 12.914 $ (−27%) | 9.755 $ (−19%) | 12.597 $ (−27%) | 65 (20%) |
| **U esempio utente**: long sopra SMA200 1D, inversione a 2 chiusure 4h oltre la EMA50 | 66.137 $ (−54%) | 6.954 $ (−59%) | **6.345 $ (−65%)** | 4.412 $ (−75%) | 455 (25%) |
| U con tetto di rischio 25% | 51.790 $ (−41%) | 8.525 $ (−44%) | 7.145 $ (−60%) | 6.092 $ (−62%) | 455 (25%) |
| Buy & hold | 21.046 $ (−81%) | 14.590 $ (−77%) | 15.425 $ (−53%) | 22.549 $ (−77%) | 1 |
| **W3.2** (ha visto tutto il 2021–26) | 25.142 $ (−37%) | 33.477 $ (−19%) | 23.488 $ (−21%) | **78.474 $ (−21%)** | 13 (92%) |

Criteri (PREREG §6): R1 0 su 4 nel giudizio, p = 0,18; R2 1 su 4, p = 0,13; U 0 su 4 nel giudizio, p = 0,15 (soglia 0,025).
**Nessuna valida.** Mappa dei vicini di R1 (S = CAGR/DD, uscite 4h, N = 1): scoperta SMA/EMA200 0,74/1,07 → giudizio −0,13/−0,16,
conferma 0,02/−0,03; tutta la famiglia: mediana S 0,01 → −0,11 → −0,02. Il buon 2021–23 era il bear del 2022.

### L'esempio dell'utente e le sue varianti (regime: chiusura 1D sopra la SMA200; 2 chiusure 4h)
| Media 4h | Inversione short (INV) 2021–26 | Short solo sotto la SMA200 (LS) | Solo long (LO) |
|---|---|---|---|
| EMA20 / SMA20 | 856 $ / 1.184 $ (DD −95/−93%, 700 trade) | 2.369 $ / 3.588 $ | 8.186 $ / 7.417 $ |
| EMA50 / SMA50 | 4.412 $ / 3.584 $ (−75/−80%) | 6.777 $ / 6.694 $ | 17.585 $ / 13.707 $ |
| EMA100 / SMA100 | 21.977 $ / 5.680 $ (−53/−67%) | 22.366 $ / 8.732 $ | 31.338 $ / 18.388 $ |
| EMA200 / SMA200 | 50.840 $ / 26.959 $ (−50/−61%, 170 trade) | 41.477 $ / 26.523 $ | 41.589 $ / 30.379 $ (−32/−42%) |

Più la media è veloce, più trade e più perdite; l'inversione short peggiora quasi sempre il solo long; solo la media a 200 candele
4h (≈ 33 giorni) batte il buy & hold, con DD −50%. Nel 2018–20 l'inversione funzionava (mediana 45.940 $): dal 2021 no
(mediana 6.793 $ e 7.455 $ nei due periodi). WR 17–29% ovunque.

### Quanto vale il migliore per caso (scoperta 2021–23)
- Miglior regola valida: S 2,60 (58.555 $). Su 200 serie rimescolate a blocchi di 20 giorni il migliore ha S mediano 1,13 e
  supera 2,60 nel 6% dei casi; White reality check p = 0,09 contro zero, p = 0,35 contro il buy & hold. **Il vincitore non è
  distinguibile dal caso.**
- Nell'insieme però le medie sui dati veri fanno meglio che sui dati rimescolati: 66% di regole positive contro 15% (p = 0,02),
  49% sopra il buy & hold contro 6% (p = 0,02). BTC ha tendenze più lunghe di 20 giorni e le medie le seguono: è il vantaggio
  generico del trend, non di una regola.
- Famiglie: solo 3 su 87 ammesse (tutte "solo short a 4h", punteggio mediano 0,000 e 0,000: parità → giudicate entrambe).

### Le regole buone restano buone?
- Correlazione di rango di S fra scoperta e giudizio: 0,52 su tutte, **0,24 fra le regole valide** in scoperta; fra famiglie 0,65.
  Regge la struttura grossa (lento e long meglio di veloce e short), non la classifica fine. Scoperta–conferma: 0,21.
- Prime 20 della scoperta: mediana 39.061 $ → 15.288 $ in giudizio (buy & hold 15.425 $), DD mediano −47% (da −25% a −61%); 1 su 20 passa i criteri.
- Regole con CAGR > 0, S > buy & hold e DD ≥ −35%: 13,9% scoperta, 14,6% giudizio, 6,0% conferma; in tutti e tre: 14 su 4.017.

| Mediana di S (scoperta / giudizio / conferma) | | Capitale mediano in giudizio | Trade/anno | WR |
|---|---|---|---|---|
| Solo long | 0,40 / 0,27 / 0,72 | 12.851 $ | 7 | 30% |
| Long + short con regime | 0,27 / 0,14 / 0,43 | 11.977 $ | 12 | 29% |
| Inversione (esempio utente) | 0,07 / 0,07 / 0,63 | 10.948 $ | 20 | 27% |
| **Solo short** | **−0,07 / −0,07 / −0,08** | 9.358 $ | 5 | 28% |
| Uscita su chiusure 1D | 0,31 / 0,16 / 0,34 | 12.114 $ | 5 | 30% |
| Uscita su chiusure 4h | 0,03 / −0,05 / 0,44 | 9.539 $ | 24 | 25% |
| Uscita su incrocio di medie | 0,15 / 0,16 / 0,27 | 11.680 $ | 4 | 40% |
| Uscita a stop/trailing ATR | 0,26 / 0,02 / 0,10 | 10.176 $ | 5 | 39% |
| EMA / SMA | 0,21 / 0,13 / 0,31 · 0,11 / 0,03 / 0,41 | 11.385 $ · 10.297 $ | 9 | 28% |
(Buy & hold: S 0,18 / 0,31 / 0,35.)
- **Gli short non funzionano**: mediana negativa in tutti e tre i periodi. **4h contro 1D**: a parità di tutto il resto l'uscita 4h
  è peggiore nel 72% delle coppie in scoperta e nel 65% in giudizio (migliore nel 57% nel 2018–20). **EMA contro SMA**: in coppia
  EMA migliore nel 59%, 51%, 34% dei casi: nessuna differenza stabile. **2–3 chiusure**: sul 4h N = 3 è meno peggio di N = 1
  (−0,15 → 0,05 in giudizio) perché dimezza i trade; sul giornaliero nessuna differenza (0,17 / 0,17 / 0,15).
- Le famiglie migliori sono le "solo long con uscita giornaliera" (es. regime EMA200 1D: 19.800 $, 15.875 $, 23.425 $ nei tre
  periodi contro 14.590 $, 15.425 $, 21.046 $ del buy & hold, DD −39/−35/−51%): circa il buy & hold con metà drawdown, molto sotto W3.2.

### Dentro W3.2 (3 varianti fissate prima)
| | 2018–20 | 2021–23 | 2024–26 | 2021–26 | Trade (WR) |
|---|---|---|---|---|---|
| W3.2 | 25.142 $ (−37%) | 33.477 $ (−19%) | 23.488 $ (−21%) | 78.474 $ (−21%) | 13 (92%) |
| K1 uscita + filtro: chiusura 4h oltre la SMA200 4h | 24.007 $ (−33%) | 22.453 $ (−26%) | 20.721 $ (−23%) | 46.433 $ (−26%) | 26 (50%) |
| K2 solo filtro d'ingresso | 25.142 $ | 28.460 $ (−21%) | 23.488 $ | 66.713 $ (−21%) | 13 (92%) |
| K3 uscita + filtro: 2 chiusure 4h oltre la EMA50 4h | 19.337 $ (−35%) | 15.243 $ (−17%) | 11.916 $ (−17%) | 18.164 $ (−17%) | 38 (45%) |
Nessuna batte W3.2: un'uscita sulle medie a 4h taglia i grandi trend (come le lezioni 109, 114, 116).

## Parte A · atlante (2018–20, 2021–23, 2024–26)
360 eventi (4h, 1D, 1W × EMA/SMA 20–200, più EMA21 e SMA40 settimanali), 712 test a 7 e 30 giorni; tabelle in `atlante.csv` e
`atlante_sintesi.csv`. Eccesso = rendimento medio dopo l'evento meno la media di quel periodo (a 30 giorni: +5,6%, +2,3%, +2,7%).
**Ricorrenti** (stesso segno nei tre periodi a 7 e 30 giorni): 18 su 204 eventi con abbastanza casi, cioè quanti se ne attendono
per caso (fra 6 e 51). Con p < 0,05: 25 a 7 giorni e 8 a 30 giorni su 356 (attesi circa 18 per orizzonte); nessuno supera la soglia corretta (0,00007).

### Le 10 regolarità più ricorrenti (eccesso a 30 giorni nei tre periodi)
1. **Un attraversamento è un falso segnale due volte su tre**: la chiusura torna dall'altro lato entro 10 barre nel 64–69% dei
   casi su 4h e 1D, in tutti i periodi; con 2 chiusure 53–60%, con 3 chiusure 48–52%. È l'unica regolarità davvero stabile.
2. Uno stato dura poco: mediana 0,7 giorni fra due attraversamenti sul 4h, 5 giorni sul giornaliero; win rate delle regole 25–30%.
3. Allineamento rialzista dei tre intervalli sopra la EMA200 (39% del tempo): +3,9 / +2,5 / +1,7 punti (p = 0,21).
4. Lo stesso con SMA50, SMA200, EMA50: +2,2…+6,9 / +1,4…+3,2 / +0,9…+2,3 (p 0,23–0,31).
5. Tre chiusure giornaliere sotto la SMA100: −12,5 / −6,1 / −2,7 (8–12 casi per periodo; p = 0,065; a 7 giorni p = 0,013).
6. Pendenza della EMA50 giornaliera che gira al ribasso: −11,4 / −2,4 / −1,9 (p = 0,052).
7. Tre chiusure giornaliere sotto la EMA50: −7,5 / −0,6 / −1,2 (p = 0,17).
8. Chiusura settimanale sotto la SMA20 settimanale: a 7 giorni −7,9 / −5,1 / −2,7 (p = 0,016), a 30 giorni −6,4 / −0,8 / −9,7.
9. Ingresso nell'allineamento ribassista (EMA20, EMA50): −3,7 / −2,4 / −0,3 e −2,3 / −3,1 / −1,7 (p 0,35–0,45).
10. Il ritest che "tiene" da sopra (4h EMA/SMA100, 1D EMA50) è seguito da rendimenti SOTTO la media: −1,8…−6,3 / −0,7…−2,7 /
    −0,7…−6,2. In generale i segnali ribassisti (13 su 18 ricorrenti) sono più regolari di quelli rialzisti, ma non si
    trasformano in short redditizi dopo costi e falsi segnali.

### Le 10 credenze che NON reggono
1. **Golden cross 50/200 giornaliero**: 9 casi in 9 anni; SMA a 7 giorni −2,2 / −4,7 / −4,5, a 30 giorni −1,9 / +6,2 / +8,2
   (p = 0,49). Death cross SMA: +2,1 / −6,3 / +0,4; EMA: +7,4 / +9,4 / −9,2. Non verificabile, segno instabile.
2. **Chiusura sopra la SMA200 giornaliera = rialzo**: −13,1 / +3,4 / −0,5 a 30 giorni; annullata entro 10 giorni nel 29% / 67% / 71%.
3. **EMA meglio della SMA**: differenza mediana di S −0,10 / +0,04 / +0,005; falsi segnali uguali (EMA 62–70%, SMA 56–65%).
4. **2–3 chiusure di conferma**: meno falsi segnali ma stesso rendimento dopo (1D, 3 chiusure sopra: −7,5 / +1,9 / +2,0; primo
   attraversamento: −7,5 / +1,3 / 0,0): si entra più tardi allo stesso valore atteso.
5. **Ritest della media che tiene = continuazione**: 1D −10,6 / −0,8 / −4,7 (mediana sulle 8 medie); 4h −1,3 / −0,9 / +0,4.
6. **Stiramento estremo = rientro**: sul giornaliero dopo uno stiramento alto +3,8 / +9,4 / +2,1 (continua, non rientra); dopo
   uno basso +1,0 / −6,8 / +1,8. Nessun p < 0,19.
7. **Ingresso nell'allineamento dei tre intervalli = continuazione**: EMA50 −1,0 / −0,8 / +1,4; SMA200 −6,2 / +5,1 / +3,5. Conta
   (poco) lo stato, non il momento in cui si forma.
8. **Pendenza che gira al rialzo**: 1D −8,5 / +1,9 / +2,2; 1W +8,9 / −0,8 / −0,4.
9. **Perdita della EMA20/21 settimanale = fine del trend**: −13,8 / +2,2 / −9,5 (6–8 casi per periodo, p = 0,10); annullata entro
   10 settimane nel 75% / 50% / 63%. Indizio, non regola: W3.2 la usa già insieme a flusso e regime.
10. **SMA200 settimanale come pavimento**: 9 chiusure sotto in 9 anni (1 / 5 / 3), poi +22,5 / +7,7 / +11,0 (p = 0,087); ritest
    che tiene: 6 casi. Coerente con un rimbalzo, non dimostrabile.

## Cosa mostrare in dashboard (solo contesto)
Una riga "Stato delle medie" per 4h, giornaliero e settimanale: chiusura sopra/sotto EMA20, EMA50, EMA200 e SMA200, con
l'etichetta "allineati al rialzo / al ribasso / misti". Dicitura: "Contesto, non segnale. Dal 2018 con i tre intervalli sopra la
EMA200 il rendimento a 30 giorni è stato di 2–4 punti sopra la media (non significativo); un attraversamento viene annullato entro
10 candele due volte su tre." Nessuna freccia operativa, nessun avviso.

## Limiti e deviazioni
- **Parità fra due famiglie** al punteggio 0,000 (caso non previsto): giudicate entrambe (R1 = quella presa dal codice, R2).
- La regola di ammissione (≥ 15 trade in tre anni e DD ≥ −35% per metà dei membri) ha ammesso solo famiglie short a 4h: le
  famiglie lente solo long (le migliori in mediana grezza) erano escluse dalla scelta. Sono riportate come descrizione: in
  giudizio stanno a 14–16.000 $ con DD −35/−43% e nel 2018–20 hanno DD −49/−51%: non avrebbero superato i criteri.
- Atlante: 360 eventi e 712 test (dichiarato "circa 500 × 2"). Una delle 200 serie rimescolate ha dato un capitale negativo su
  uno short (S non calcolabile): contata come non superiore. Funding: usato f_long (uguale a f_repo dal 2020; zero prima).
- Grammatica di 4.017 regole e commit della preregistrazione: richiesti dall'incarico (oltre le 8 varianti abituali).
- Le varianti K leggono lo stato 4h alla chiusura giornaliera. Short a prezzo spot (base ignorata). Periodi come fette di una
  curva continua. Tre periodi di tre anni = pochi cicli indipendenti: un pattern "ricorrente" su tre periodi resta debole.
- W3.2 non è fuori campione sul 2024–26; le regole di questo studio sì.

## File
`PREREG.md` · `fetch.py` · `es_lib.py` (medie, grammatica) · `es_engine.py` (motore 4h; verificato con un ciclo indipendente: 16.247,6 $
in entrambi) · `es_scoperta.py` → `scoperta.txt`, `scoperta.csv`, `famiglie.csv`, `scelta.json`, `rc_scoperta.json`,
`caso_scoperta.csv` · `es_giudizio.py` → `giudizio.txt`, `risultati.csv`, `giudicate.csv`, `esempio_utente.csv`, `p_giudizio.csv`,
`tetto25.csv`, `mappa_*.csv`, `ok_tre_periodi.csv`, `w32_k.csv` · `es_w32.py` · `es_atlante.py` → `atlante.csv`,
`atlante_sintesi.csv` · `es_dati.py` → `DATI.md`, `DATI-giornaliero.md`, `DATI-4h.md`, `data/*.csv.gz`.

## Lezione proposta (117)
**Lezione 117**: EMA e SMA su 4h, giornaliero e settimanale (research/ema_sma, PREREG 9a33184; 4.017 regole regime × innesco ×
uscita × lato, scoperta 2021–23, giudizio 2024–26, conferma 2018–20). Nessuna regola valida: la scelta perde in giudizio (8.584 $,
DD −41%), l'esempio "long sopra la SMA200 giornaliera, inversione short a 2 chiusure 4h sotto una media" fa 10.000 → 4.412 $
(DD −75%, 455 trade, WR 25%); il migliore della scoperta non si distingue dal caso (p 0,06–0,35) e la classifica non si conserva
(rango 0,24). Regge solo il fatto generico già noto: medie lente giornaliere long/flat ≈ buy & hold con metà drawdown. Short su
medie: mediana negativa in tutti i periodi; uscite a 4h peggiori di quelle giornaliere (24 trade l'anno, WR 25%); EMA = SMA; 2–3
chiusure riducono i falsi segnali ma non il rendimento; un attraversamento è annullato entro 10 barre due volte su tre. Golden
cross, ritest, stiramenti, pendenze: 18 eventi "ricorrenti" su 204, quanti per caso. Dentro W3.2 un'uscita o un filtro a 4h
peggiorano (46.433 $ e 66.713 $ contro 78.474 $). Le medie restano contesto visivo (stato sui tre intervalli), non segnale.
