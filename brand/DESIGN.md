# RadarSignal · sistema di design

## 1. Spunti da CoinTracker (dashboard) (pagine pubbliche: home, /portfolio-tracker; CSS pubblico)

| Aspetto | CoinTracker | Cosa prendiamo, cosa no |
|---|---|---|
| Font | proprietario "Cointracker Pro", fallback Inter; mono per le cifre | **Inter** (Google Fonts, libero) con cifre tabellari; Geist Mono solo per orari |
| Palette | grigi neutri (sfondo `#fcfcfd`, card bianche, bordo ~`#e5e5e5`, testo muto ~`#737373`); verde `oklch(61% .15 150)`, rosso `oklch(58% .25 27)`; accenti viola e lime | neutri freddi + **indaco del brand** al posto di viola/lime; verde e rosso più scuri per il contrasto AA su bianco |
| Raggi | base 10px, card 16–24px, controlli a pillola | card 20px, tessere 14px, controlli a pillola |
| Ombre | quasi assenti, bordi sottili | bordo 1px + ombra leggerissima; ombra marcata solo per tab bar e pannelli |
| Densità | molto spazio, titoli grandi, etichette in minuscolo | stessa aria, ma più dati per schermata: è un tool, non una landing |
| Grafici | linee morbide, aree sfumate, niente griglie verticali | aree nel colore del brand, solo griglia orizzontale |

## 2. Token (variabili CSS su `:root`, tema scuro su `:root[data-theme="dark"]`)

Tema **chiaro di base**; lo scuro si sceglie con il pulsante luna in alto (salvato in `localStorage.radarTheme`).

| Token | Chiaro | Scuro | Uso |
|---|---|---|---|
| `--bg` | `#f4f5f7` | `#0c0d10` | fondo pagina |
| `--card` / `--bg2` | `#ffffff` | `#15171c` / `#111317` | card, sidebar |
| `--raise` / `--fill` | `#f2f4f7` | `#1e2128` | tessere interne, controlli |
| `--line` / `--line2` | `#e6e8ec` / `#d5d9e0` | `#252931` / `#333843` | bordi, separatori |
| `--label` / `2` / `3` | `#0f1218` / `#555c68` / `#878e99` | `#f1f3f7` / `#a3aab6` / `#717884` | testo primario, secondario, etichette |
| `--tint` | `#2f4cf0` | `#7088ff` | brand, link, voce attiva |
| `--green` / `--green-bg` | `#0f8a4a` / `#e8f6ee` | `#3fd185` / 12% | guadagno, long |
| `--red` / `--red-bg` | `#d6342a` / `#fdecea` | `#ff6b5f` / 12% | perdita, short, stop |
| `--orange` | `#c96a00` | `#f5a23a` | avvisi, SMA 40 |

| Tipografia | Valore |
|---|---|
| Prezzo (hero) | Inter 700, `clamp(2.3rem, 10vw, 3.4rem)`, −0,04em |
| Numero chiave di card (P&L, rendimento) | Inter 700, 2,5rem |
| Valori di tessera | Inter 600–650, 1,2–1,4rem |
| Titolo sezione | Inter 600, 1,06rem |
| Testo | Inter 400, 0,95rem / 1,5 |
| Etichette | Inter 500, 0,72–0,8rem, **minuscolo**, colore `--label3` |

| Spazi e forme | Valore |
|---|---|
| Spaziatura | multipli di 4px; gap sezioni 24px, padding card 20px, tessere 14×16px |
| Raggi | `--r-card` 20px, `--r-tile` 14px, `--r-ctl` 999px |
| Ombre | `--shadow` 0 1px 2px / 0 1px 3px a 4–5%; `--shadow-lg` per tab bar e pannelli |

## 3. Componenti

| Componente | Regola |
|---|---|
| `.card`, `.list`, `.tiles`, `.big` | bianco su fondo neutro, bordo 1px, ombra leggera; niente bagliori |
| Stato (`.status`, `.wkBadge`) | pillola con fondo tenue del colore di stato (verde long, rosso short, indaco segnale) |
| `.seg` | binario grigio, opzione attiva = pillola bianca con ombra |
| Navigazione | sidebar bianca su desktop (voce attiva indaco tenue); tab bar flottante su telefono |
| Logo | vedi sezione 4: simbolo "Eco" in `--tint` (o bianco su indaco/nero), wordmark `radar` + `signal` in `--tint` |
| Grafici | candele verde/rosso di stato, EMA indaco, SMA arancio tratteggiata, aree `--tint` al 22% |
| Icone | tratto 1,7px, angoli arrotondati, 20–22px, `currentColor` |

## 4. Brand (sorgenti in `brand/src`, render con `node brand/src/render.js`)

Spunti (reference dell'utente, solo lo spirito): nexaris → simbolo geometrico spesso, bianco su blu pieno, wordmark sans
minuscolo bold; DetectHub → moduli pieni, bianco su nero. Nessuna forma ripresa: niente tratti a zig-zag, niente cerchi a incastro.
Confronto delle tre proposte in `src/varianti.png` (A sweep a tratto: si legge "G"; B quadranti: sembra una torta; **C Eco: scelta**).

| Elemento | Regola |
|---|---|
| Simbolo "Eco" | griglia 64, centro 32,32: sorgente r 6, anello r 12,5–19, anello r 24–31; entrambi aperti da un fascio radiale di 30° verso nord-est (da −60° a −30°). Un solo colore, nessun gradiente. Il fascio è il segnale che esce, gli anelli l'eco radar. File: `src/mark.svg` (`currentColor`) |
| Tile / icona app | quadrato indaco pieno `#2f4cf0`, raggio 22%, segno bianco al 62%. `icon.svg` e favicon: segno al 72% (correzione ottica per 16–32 px) |
| Wordmark | `radarsignal` tutto minuscolo, Inter 700, −0,045em. Minuscolo come nelle reference: più amichevole e compatto, e coincide con l'intestazione della dashboard; le due parole si separano col colore (`radar` Ink, `signal` `--tint`), non con la maiuscola. "RadarSignal" resta la grafia nel testo corrente |
| Lockup | segno alto 1,1× il corpo del wordmark, distanza 0,3× il corpo. Variante con tile (avatar, app) solo dove serve un quadrato |
| Versioni | chiara (`logo-light.png`: segno e `signal` indaco su bianco); **indaco pieno** e **nero** (`logo-dark.png`, fondo `#0c0d10`): tutto bianco, un solo colore. Tema scuro della dashboard: `--tint` `#7088ff` |
| Copertina | `banner.png` (chiara) e `social-preview.png` (scura), 1280×640: lockup, titolo “Segnali chiari su Bitcoin.”, frase di valore, tre fatti di prodotto, mock astratto senza cifre, cerchi radar come motivo |

| Palette | Hex | Uso |
|---|---|---|
| Signal Indigo | `#2f4cf0` | colore di marca, fondo pieno, `--tint` chiaro |
| Indigo Night | `#7088ff` | `--tint` scuro |
| Ink / Night / Paper | `#0f1218` / `#0c0d10` / `#f4f5f7` | testo, fondo nero, fondo chiaro |
| Blip Mint | `#5ef0c4` | solo l'ultimo punto dei grafici; mai nel logo né nel testo |
| Stato | `#0f8a4a` / `#d6342a` / `#c96a00` | long, short, avviso: mai come colori di marca |

**Area di rispetto**: margine libero x = 30% del lato del segno (o della tile). **Misure minime**: segno 16 px, lockup con segno 20 px.
**Da evitare**: ruotare il segno (il fascio punta sempre a nord-est), chiudere o spostare il fascio, aggiungere gradienti o un
secondo colore al segno, contorni, ombre, wordmark con maiuscole, numeri di performance nelle copertine.
