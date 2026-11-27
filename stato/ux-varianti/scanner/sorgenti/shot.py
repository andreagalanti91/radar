"""shot.py TEMPLATE OUTDIR PREFIX [ACTIONS]: render R_full.json con radar.dashboard.render usando TEMPLATE, screenshot #scanner
400/1280 chiaro/scuro (scale 2), overflow orizzontale ed errori JS. ACTIONS: js da eseguire dopo l'apertura per lo scatto "_open"."""
import sys, json, threading, functools, http.server
from datetime import datetime
from pathlib import Path
sys.path.insert(0, "/home/user/radar")
import radar.dashboard as RD
from playwright.sync_api import sync_playwright
D = Path(__file__).resolve().parent.parent
TPL, OUT, PFX = Path(sys.argv[1]), Path(sys.argv[2]), sys.argv[3]
ACT = sys.argv[4] if len(sys.argv) > 4 else ""
OUT.mkdir(parents=True, exist_ok=True)
RD.TEMPLATE = TPL
site = D / ("site_" + PFX); site.mkdir(exist_ok=True)
RD.render(json.loads((D / "R_full.json").read_text()), site / "index.html")
class Q(http.server.SimpleHTTPRequestHandler):
    def log_message(self, *a): pass
srv = http.server.ThreadingHTTPServer(("127.0.0.1", 0), functools.partial(Q, directory=str(site)))
threading.Thread(target=srv.serve_forever, daemon=True).start()
url = f"http://127.0.0.1:{srv.server_port}/index.html"
errs = []
with sync_playwright() as p:
    b = p.chromium.launch()
    for theme in ("dark", "light"):
        for w in (360, 400, 1280):
            ctx = b.new_context(viewport={"width": w, "height": 900}, device_scale_factor=2, color_scheme=theme)
            ctx.add_init_script(f"try{{localStorage.setItem('radarTheme','{theme}')}}catch(e){{}}")
            pg = ctx.new_page()
            pg.route("**/*", lambda r: r.continue_() if "127.0.0.1" in r.request.url else r.abort())
            pg.on("pageerror", lambda e, w=w, t=theme: errs.append(f"{t} {w} pageerror {e}"))
            pg.on("console", lambda m, w=w, t=theme: m.type == "error" and "ERR_FAILED" not in m.text and "WebSocket" not in m.text and errs.append(f"{t} {w} console {m.text}"))
            pg.goto(url + "#oggi", wait_until="networkidle")
            pg.evaluate("location.hash='#scanner'"); pg.wait_for_timeout(1500)
            info = pg.evaluate("""() => ({sw: document.documentElement.scrollWidth, cw: document.documentElement.clientWidth,
              over: [...document.querySelectorAll('#v-scanner *')].filter(e => { const r = e.getBoundingClientRect(); return e.offsetParent && r.width && r.right > document.documentElement.clientWidth + 1 && !e.closest('.scroll,.scPills'); }).map(e => e.id || e.className).slice(0, 6)})""")
            print(theme, w, json.dumps(info, ensure_ascii=False))
            if w != 360:
                pg.screenshot(path=str(OUT / f"{PFX}_{w}_{theme}.png"), full_page=True)
            if ACT:
                pg.evaluate(ACT); pg.wait_for_timeout(500)
                info = pg.evaluate("() => [document.documentElement.scrollWidth, document.documentElement.clientWidth]")
                print(theme, w, "open", info)
                if w != 360:
                    el = pg.query_selector("#scPos")
                    (el or pg).screenshot(path=str(OUT / f"{PFX}_dettagli_{w}_{theme}.png"))
            ctx.close()
    b.close()
print("ERRORI JS:", errs or "nessuno")
