# Radar Signal · sistema di design

## 1. Spunti da CoinTracker (pagine pubbliche: home, /portfolio-tracker; CSS pubblico)

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
| Logo | segno Radar in una tessera con il gradiente del brand (`#3d5bff` → `#8b5cff`, punto menta `#5ef0c4`) |
| Grafici | candele verde/rosso di stato, EMA indaco, SMA arancio tratteggiata, aree `--tint` al 22% |
| Icone | tratto 1,7px, angoli arrotondati, 20–22px, `currentColor` |
