# Tool: moduli principali (radar/) — giro orario in .github/workflows/daily.yml
- cli.py (giro), weekly.py (W3.2 + avvisi Telegram), preview.py (Pre-analisi: soglie della prossima chiusura, posizione, contesto di oggi),
  telegram.py (avvisi e riepilogo giornaliero "Oggi" all'01:00 italiana), journal.py + xinbox.py (comandi bot, post del trader).
- Dati: data.py (Binance archivio + OKX provvisorio), features.py (pf14z, sf14z), liqmap/liqsnap/liqsources/liqcascade (liquidazioni:
  mappa = STIMA; reali: eventi e livelli on-chain Hyperliquid/Lighter), liqstream.py (raccoglitore per VM europea, non attivo).
- Dashboard: dashboard_template.html + pages/*.html; sezioni Oggi, Storico, Liquidazioni, Wallet, News.
- Test: tests/ (unittest, NON pytest): `python3 -m unittest discover -s tests -q` (273 OK al 22/11).
- Dal 22/11: macro.py (chiusura giornaliera multi-asset, report.macro), pages/book.html (heatmap del book, solo browser), Wallet in pausa (RADAR_WALLETS=0, tab nascosta).
- Dal 22/11 anche: guard.py (soglie d'allarme), provlog.py (provvisori vs definitivi), coherence.py (controlli di coerenza orari): solo avvisi.
- Dal 23/11: context.py (riquadro "Contesto" in Oggi, report.context: trend su media a 200 giorni, volatilità, tasso Fed, bilancio/liquidità netta, CPI, VIX, FOMC; FRED 1 volta al giorno, cache data/context.csv; SOLO descrizione, niente probabilità, nessun effetto su W3.2 — lezione 113; tests/test_context.py).
