"""Genera la dashboard statica (site/index.html) con i dati embeddati."""
from __future__ import annotations

import json
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).with_name("dashboard_template.html")
BRAND = ROOT / "brand"
MANIFEST = {
    "name": "Radar Signal BTC", "short_name": "Radar Signal", "start_url": "./#oggi", "display": "standalone",
    "background_color": "#000000", "theme_color": "#000000",
    "icons": [{"src": "icon-192.png", "sizes": "192x192", "type": "image/png"},
              {"src": "icon-512.png", "sizes": "512x512", "type": "image/png"}],
}

HEAD = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover, interactive-widget=resizes-content">
<meta name="theme-color" media="(prefers-color-scheme: light)" content="#f2f2f7">
<meta name="theme-color" media="(prefers-color-scheme: dark)" content="#000000">
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
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", json.dumps(report, default=str))
    out.write_text((HEAD + html + "\n</body>\n</html>\n") if standalone else html)
    if standalone:
        for name in ("icon.svg", "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
            shutil.copy(BRAND / name, out.parent / name)
        (out.parent / "manifest.webmanifest").write_text(json.dumps(MANIFEST, indent=1))
        # notizie anche come file separato: la pagina le ricarica senza dover essere rigenerata
        (out.parent / "news.json").write_text(json.dumps({"news": report.get("news", []), "calendar": report.get("calendar", [])}))
    return out
