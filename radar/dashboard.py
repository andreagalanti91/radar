"""Genera la dashboard statica (site/index.html) con i dati embeddati."""
from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).with_name("dashboard_template.html")

HEAD = """<!doctype html>
<html lang="it">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
</head>
<body>
"""


def render(report: dict, out: Path | None = None, standalone: bool = True) -> Path:
    out = out or ROOT / "site" / "index.html"
    out.parent.mkdir(parents=True, exist_ok=True)
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", json.dumps(report, default=str))
    out.write_text((HEAD + html + "\n</body>\n</html>\n") if standalone else html)
    return out
