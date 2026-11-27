"""Genera la dashboard statica (site/index.html) con i dati di Oggi incorporati e i file JSON delle pagine secondarie accanto."""
from __future__ import annotations

import hashlib
import json
import os
import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TEMPLATE = Path(__file__).with_name("dashboard_template.html")
PAGES = Path(__file__).with_name("pages")   # pagine separate: Liquidazioni (spenta: LIQ_ON nel template), Book (spento: BOOK_ON), Wallet reale (wallet.html), wallet Hyperliquid (in pausa, hyperliquid.html); HTML + script che si registra in window.PAGES
BRAND = ROOT / "brand"
WALLET_CONFIG = Path(__file__).with_name("wallet_config.json")   # Wallet reale: URL Supabase e chiave pubblica (supabase_config)
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
    report, files = split(report)
    # file secondari accanto a index.html (prima della pagina: chi apre la pagina nuova trova già i suoi file)
    for name, body in files.items():
        (out.parent / name).write_text(body)
    pages = "\n".join(f.read_text() for f in sorted(PAGES.glob("*.html"))) if PAGES.exists() else ""
    html = TEMPLATE.read_text().replace("/*__DATA__*/null", json.dumps(report, default=str)).replace("<!--__PAGES__-->", pages)
    html = html.replace("/*__SUPABASE__*/null", json.dumps(supabase_config()).replace("</", "<\\/"))
    html = html.replace("/*__BUILD__*/null", json.dumps(build_info()).replace("</", "<\\/"))
    out.write_text((HEAD + html + "\n</body>\n</html>\n") if standalone else html)
    if standalone:
        for name in ("icon.svg", "favicon-32.png", "apple-touch-icon.png", "icon-192.png", "icon-512.png"):
            shutil.copy(BRAND / name, out.parent / name)
        (out.parent / "manifest.webmanifest").write_text(json.dumps(MANIFEST, indent=1))
    return out


def build_info() -> dict:
    """Versione mostrata nel Profilo: commit corto del codice (GITHUB_SHA nel workflow, altrimenti git locale; None se non disponibile)."""
    sha = os.environ.get("GITHUB_SHA", "").strip()[:7] or None
    if not sha:
        import subprocess
        try:
            r = subprocess.run(["git", "rev-parse", "--short=7", "HEAD"], cwd=ROOT, capture_output=True, text=True, timeout=3)
            sha = r.stdout.strip() or None if r.returncode == 0 else None
        except (OSError, subprocess.SubprocessError):
            sha = None
    return {"commit": sha}


def supabase_config() -> dict | None:
    """Accesso del Wallet reale (radar/pages/wallet.html, supabase/LEGGIMI.md): URL del progetto e chiave anon/publishable da
    radar/wallet_config.json (override: RADAR_SUPABASE_URL e RADAR_SUPABASE_ANON, entrambe), pubblica per design
    (la sicurezza la dà la Row Level Security di supabase/schema.sql). Mai la chiave service_role. None = Wallet non configurato."""
    url, anon = os.environ.get("RADAR_SUPABASE_URL", "").strip(), os.environ.get("RADAR_SUPABASE_ANON", "").strip()
    if not (url and anon) and WALLET_CONFIG.exists():   # file pubblico nel repo; le variabili d'ambiente, se presenti, lo sostituiscono
        try:
            c = json.loads(WALLET_CONFIG.read_text())
            url, anon = str(c.get("url") or "").strip(), str(c.get("anon") or "").strip()
        except (ValueError, OSError) as e:
            print(f"[dashboard] radar/wallet_config.json non leggibile: {e!r}")
            return None
    if not (url.startswith("https://") and anon):
        return None
    if _secret_key(anon):
        print("[dashboard] RADAR_SUPABASE_ANON contiene una chiave segreta (service_role): Wallet lasciato non configurato")
        return None
    return {"url": url.rstrip("/"), "anon": anon}


def _secret_key(k: str) -> bool:
    """True per le chiavi che non devono mai finire nella pagina: sb_secret_… o JWT con ruolo service_role."""
    if k.startswith("sb_secret_"):
        return True
    parts = k.split(".")
    if len(parts) == 3:
        import base64
        try:
            body = json.loads(base64.urlsafe_b64decode(parts[1] + "=" * (-len(parts[1]) % 4)))
            return body.get("role") != "anon"
        except Exception:  # noqa: BLE001
            return False
    return False


# ---- pagina leggera (26/11/2026): nella pagina restano i dati di Oggi e di Posizioni; i dati pesanti delle pagine secondarie vanno
# in file JSON accanto a index.html, che la pagina scarica alla prima apertura di quella pagina (window.lazyData nel template) e
# unisce in R. Ogni file è una "toppa" con la stessa forma del report: {"livelli": {"serie": ...}} si unisce in R.livelli.serie.
# R._lazy = {pagina: "file.json?v=impronta"}: l'impronta del contenuto evita di unire un file vecchio rimasto in cache a una pagina
# nuova. resto.json raccoglie ciò che la pagina non usa (resta pubblicato, nessuna pagina lo scarica).
LAZY_FILES = {"grafico": "grafico.json", "scanner": "scanner.json", "movimenti": "movimenti.json", "notizie": "news.json"}
RESTO = ("equity", "trades", "series", "scout", "orderbook")   # non letti dalla pagina (scout: pagina Wallet in pausa)
CHART_KEEP = 5   # weekly[_eth].chart: la pagina legge solo l'ultima chiusura e la SMA 40 di 4 settimane fa (condsHtml)


def _is_noi(n: dict) -> bool:
    """Stessa regola di isNoi nel template: notizie "per noi" (le uniche che servono a Oggi)."""
    return n.get("group") == "noi" if n.get("group") else n.get("level") != "basso"


def split(report: dict) -> tuple[dict, dict[str, str]]:
    """(report per la pagina, {nome file: contenuto JSON}). Non modifica il report ricevuto."""
    r, files, resto = dict(report), {}, {}
    lazy = {k: {} for k in LAZY_FILES}

    def dump(o) -> str:
        return json.dumps(o, default=str, separators=(",", ":"))

    for k in RESTO:
        if k in r:
            resto[k] = r.pop(k)
    s = resto.get("series")
    if isinstance(s, dict) and s.get("date"):
        r["series_start"] = s["date"][0]   # prima data dello storico giornaliero (simulatore senza W3.2)
    if isinstance(r.get("livelli"), dict) and "serie" in r["livelli"]:   # candele 1D del Grafico
        r["livelli"] = dict(r["livelli"])
        lazy["grafico"]["livelli"] = {"serie": r["livelli"].pop("serie")}
    for k in ("scanner", "trx_carta", "scommesse", "emergenti_carta"):
        if k in r:
            lazy["scanner"][k] = r.pop(k)
    for key in ("weekly", "weekly_eth"):
        W = r.get(key)
        if not isinstance(W, dict):
            continue
        W = r[key] = dict(W)
        if isinstance(W.get("chart"), dict):
            resto.setdefault(key, {})["chart"] = W["chart"]
            W["chart"] = {k: v[-CHART_KEEP:] if isinstance(v, list) else v for k, v in W["chart"].items()}
        H = W.get("history")
        if isinstance(H, dict):
            H = W["history"] = dict(H)
            for k in ("eq_dates", "eq1", "eq2"):
                if k not in H:
                    continue
                v = H.pop(k)
                if key == "weekly" and k in ("eq_dates", "eq1"):   # equity giornaliera: simulatore e Dettagli in Movimenti
                    lazy["movimenti"].setdefault("weekly", {}).setdefault("history", {})[k] = v
                else:
                    resto.setdefault(key, {}).setdefault("history", {})[k] = v
    if isinstance(r.get("news"), list):   # Oggi usa solo le notizie "per noi"; la pagina Notizie le scarica tutte da news.json
        lazy["notizie"] = {"news": r["news"], "calendar": r.get("calendar", []), "banks": r.get("banks", [])}
        r["news"] = [n for n in r["news"] if isinstance(n, dict) and _is_noi(n)]
    else:   # news.json c'è sempre: la pagina lo ricarica ogni 10 minuti
        files["news.json"] = dump({"news": [], "calendar": r.get("calendar", []), "banks": r.get("banks", [])})
    r["_lazy"] = {}
    for k, body in lazy.items():
        if not body:
            continue
        txt = dump(body)
        files[LAZY_FILES[k]] = txt
        r["_lazy"][k] = f"{LAZY_FILES[k]}?v={hashlib.sha1(txt.encode()).hexdigest()[:10]}"
    files["resto.json"] = dump(resto)
    return r, files
