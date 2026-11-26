"""Genera la dashboard statica (site/index.html) con i dati embeddati."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).with_name("dashboard_template.html")
PAGES = Path(__file__).with_name("pages")   # pagine separate: Liquidazioni (spenta: LIQ_ON nel template), Book (spento: BOOK_ON), Wallet (in pausa); HTML + script che si registra in window.PAGES
BRAND = ROOT / "brand"
MANIFEST = {
    "name": "Radar Signal BTC", "short_name": "Radar Signal", "start_url": "./#oggi", "display": "standalone",
    "background_color": "#f4f5f7", "theme_color": "#f4f5f7",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}],
}

HEAD = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
<meta name="theme-color" content="#f4f5f7">
<meta name="color-scheme" content="light dark">
<meta name="apple-mobile-web-app-capable" content="yes">
<meta name="apple-mobile-web-app-title" content="Radar Signal">
<meta name="apple-mobile-web-app-status-bar-style" content="default">
<link rel="icon" type="image/svg+xml" href="icon.svg">
<link rel="icon" type="image/png" sizes="32x32" href="favicon-32.png">
<link rel="apple-touch-icon" href="apple-touch-icon.png">
<link rel="manifest" href="manifest.webmanifest">
</head>
<body>
"""


def render(report: dict, out: Path | None = None, standalone: bool = True) -> Path:
    out = out or ROOT / "site" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    # nell'interfaccia solo la strategia in uso (W3.2): conti su carta e candidati della ricerca restano fuori dalla pagina
    report = {k: v for k, v in report.items() if k not in ("paper", "lab")}
    jf = ROOT / "data" / "journal.json"  # registro dei trade reali via Telegram (radar/journal.py)
    if "journal" not in report and jf.exists():
        from .journal import averages, load
        j = load()
        report = dict(report, journal={"trades": j["trades"], "avg": averages(j)})
    if "journal" in report and "rvm" not in report["journal"]:   # "Reale contro modello" della pagina Movimenti
        from .journal import real_vs_model
        report = dict(report, journal=dict(report["journal"], rvm=real_vs_model(report["journal"])))
    if "limiti" not in report and report.get("weekly"):   # allarme "fuori dal backtest" (radar/limiti.py): solo calcolo
        from .limiti import status
        try:
            report = dict(report, limiti=status({"BTC": report.get("weekly"), "ETH": report.get("weekly_eth")}, report.get("journal")))
        except Exception as e:  # noqa: BLE001
            print(f"[dashboard] limiti storici non calcolati: {e!r}")
    if "scout" not in report and (ROOT / "data" / "wallet_picks.json").exists():   # balene del giorno (radar/scout.py)
        from .scout import summary
        report = dict(report, scout=summary(ROOT / "data"))
    pages = "\n".join(f.read_text() for f in sorted(PAGES.glob("*.html"))) if PAGES.exists() else ""
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", json.dumps(report, default=str)).replace("<!--__PAGES__-->", pages)
    out.write_text((HEAD + html + "\n</body>\n</html>\n") if standalone else html)
    if standalone:
        for name in ("icon.svg", "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
            shutil.copy(BRAND / name, out.parent / name)
        (out.parent / "manifest.webmanifest").write_text(json.dumps(MANIFEST, indent=1))
        # notizie anche come file separato: la pagina le ricarica senza dover essere rigenerata
        (out.parent / "news.json").write_text(json.dumps({"news": report.get("news", []), "calendar": report.get("calendar", []), "banks": report.get("banks", [])}))
    return out
