# Radar Signal · sistema di design

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
| Logo | vedi sezione 4: tile indaco con il segno bianco e blip menta, wordmark `radar` + `signal` in `--tint` |
| Grafici | candele verde/rosso di stato, EMA indaco, SMA arancio tratteggiata, aree `--tint` al 22% |
| Icone | tratto 1,7px, angoli arrotondati, 20–22px, `currentColor` |

## 4. Brand (sorgenti in `brand/src`, render con `node brand/src/render.js`)

Spunto CoinTracker (home pubblica): fondi neutri chiari, un solo colore di marca, titoli grandi e asciutti, card di prodotto
flottanti come illustrazione. Nessun elemento ripreso dal loro marchio: niente viola/lime, niente font proprietario, niente forme loro.

| Elemento | Regola |
|---|---|
| Simbolo | radar essenziale su griglia 64: anello (r 28 / 20,5), fascio a quarto di cerchio (r 17,5, ore 12→3), blip (r 4,5) in basso a sinistra. File: `src/mark.svg` (`currentColor`) |
| Tile / icona app | quadrato raggio 22%, gradiente `#5a6bff → #2f4cf0 → #2236c4` (160°), segno bianco al 60%, blip `#5ef0c4`. Favicon e `icon.svg`: segno al 68% (correzione ottica per 16–32 px) |
| Wordmark | `radarsignal` minuscolo, Inter 700, −0,04em; `radar` in Ink, `signal` Inter 600 in `--tint` (come l'intestazione della dashboard) |
| Lockup | tile alta 1,2× il corpo del wordmark, distanza 0,32× il corpo. Versioni: chiara (`logo-light.png`), scura (`logo-dark.png`, `signal` in `#7088ff`) |
| Monocromo | segno e blip nello stesso colore (Ink o bianco) per stampa, filigrane, contesti a un colore |
| Copertina | `banner.png` (chiara) e `social-preview.png` (scura), 1280×640: lockup, titolo “Segnali chiari su Bitcoin.”, frase di valore, tre fatti di prodotto, mock astratto (curva, candele, interruttore) senza cifre, cerchi radar come motivo |

| Palette | Hex | Uso |
|---|---|---|
| Signal Indigo | `#2f4cf0` | colore di marca, `--tint` chiaro |
| Indigo Night | `#7088ff` | `--tint` scuro |
| Blip Mint | `#5ef0c4` | solo il blip (mai testo: contrasto basso su bianco) |
| Ink / Paper / Night | `#0f1218` / `#f4f5f7` / `#0c0d10` | testo, fondo chiaro, fondo scuro |
| Stato | `#0f8a4a` / `#d6342a` / `#c96a00` | long, short, avviso: mai come colori di marca |

**Area di rispetto**: attorno alla tile (o al lockup) margine libero x = 30% del lato della tile; nessun testo o bordo dentro.
**Misure minime**: tile 16 px, lockup con tile 20 px. **Da evitare**: ruotare o deformare il segno, cambiare il gradiente,
mettere il wordmark senza tile in contesti piccoli, usare la menta per testo, mettere numeri di performance nelle copertine.

