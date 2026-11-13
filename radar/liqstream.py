"""Raccoglitore WebSocket delle liquidazioni REALI di BTC su Binance, Bybit e OKX (per un server FUORI dagli USA).

Perché: i runner GitHub sono negli USA, dove Binance (fapi/fstream) e Bybit sono bloccati e le loro liquidazioni non hanno un
endpoint REST pubblico; esistono solo come flussi WebSocket. Questo processo gira su una VM in Europa (guida: deploy/LIQSTREAM.md,
unit systemd: deploy/liqstream.service), salva ogni evento e ogni ora spinge sul repo i file delle ore chiuse.

Flussi (solo API pubbliche documentate, nessuna chiave per leggere):
- Binance USDT-M  wss://fstream.binance.com/stream?streams=btcusdt@forceOrder/!forceOrder@arr  (simboli BTCUSDT, BTCUSDC).
  ATTENZIONE: Binance invia al massimo UN ordine di liquidazione per simbolo ogni 1000 ms (snapshot): nelle cascate il totale
  è SOTTOSTIMATO. I due flussi possono ripetere lo stesso ordine: doppioni tolti per id.
- Bybit v5 linear  wss://stream.bybit.com/v5/public/linear, topic allLiquidation.BTCUSDT (tutte le liquidazioni, a lotti
  ogni 500 ms). Doc: "S = Buy" → è stata liquidata una posizione LONG.
- OKX            wss://ws.okx.com:8443/ws/v5/public, canale liquidation-orders (SWAP), solo BTC-USDT-SWAP; stessi id di
  radar/liqsources.parse_okx (i doppioni con la raccolta REST oraria si tolgono in liqsources.summary).

Formato: data/liq_stream/YYYY-MM-DD/HH.csv (UTC), colonne di data/liq_events (ts, exchange, id, side, price, btc, usd;
side = lato LIQUIDATO). Un file per ora: dopo la chiusura dell'ora non cambia più → nessun conflitto git con il workflow orario.
data/liq_stream/status.json: ultimo messaggio, eventi e riconnessioni per exchange (controllo di qualità lato dashboard).

Push: `git add data/liq_stream && git commit && git pull --rebase && git push` ogni ora. Credenziali SOLO da variabili d'ambiente:
  LIQSTREAM_SSH_KEY  = percorso della chiave di deploy (consigliato), oppure
  LIQSTREAM_GIT_TOKEN = token fine-grained con permesso Contents: write sul solo repo (passato a git come header via
  GIT_CONFIG_*, mai nella riga di comando né nei log).
Uso:  python -m radar.liqstream --repo /home/ubuntu/radar [--no-push] [--exchanges binance,bybit,okx]
Dipendenza in più rispetto al tool: `pip install websockets` (solo sulla VM).
"""
from __future__ import annotations

import argparse
import asyncio
import base64
import csv
import json
import logging
import os
import random
import subprocess
import time
from datetime import datetime, timezone
from pathlib import Path

from .liqsources import COLS, _ev, check, parse_okx

log = logging.getLogger("liqstream")

URLS = {
    "binance": os.environ.get("LIQSTREAM_BINANCE_URL", "wss://fstream.binance.com/stream?streams=btcusdt@forceOrder/!forceOrder@arr"),
    "bybit": os.environ.get("LIQSTREAM_BYBIT_URL", "wss://stream.bybit.com/v5/public/linear"),
    "okx": os.environ.get("LIQSTREAM_OKX_URL", "wss://ws.okx.com:8443/ws/v5/public"),
}
BINANCE_SYMBOLS = {"BTCUSDT", "BTCUSDC"}
BYBIT_TOPICS = ["allLiquidation.BTCUSDT"]
OKX_INST = "BTC-USDT-SWAP"
SUBSCRIBE = {
    "bybit": {"op": "subscribe", "args": BYBIT_TOPICS},
    "okx": {"op": "subscribe", "args": [{"channel": "liquidation-orders", "instType": "SWAP"}]},
}
APP_PING = {"bybit": (20, json.dumps({"op": "ping"})), "okx": (25, "ping")}   # ping applicativi richiesti dai due exchange
PUSH_EVERY_S = 3600
SILENCE_WARN_S = 6 * 3600   # nessun messaggio per 6 ore da un exchange: avviso nel log (il mercato calmo può tacere a lungo)


# ------------------------------------------------------------------ parser puri (tests/test_liqstream.py)
def parse_binance(msg: dict) -> list[dict]:
    """Messaggio forceOrder (anche incapsulato in {"stream", "data"} o in lista da !forceOrder@arr) → eventi BTC.

    o.S = lato dell'ordine di liquidazione: SELL chiude un long (long liquidato), BUY chiude uno short."""
    data = msg.get("data", msg) if isinstance(msg, dict) else msg
    items = data if isinstance(data, list) else [data]
    out = []
    for it in items:
        if not isinstance(it, dict) or it.get("e") != "forceOrder":
            continue
        o = it.get("o") or {}
        if o.get("s") not in BINANCE_SYMBOLS or o.get("S") not in ("BUY", "SELL"):
            continue
        qty = float(o.get("z") or o.get("l") or o.get("q") or 0)
        px = float(o.get("ap") or 0) or float(o.get("p") or 0)
        if qty <= 0 or px <= 0:
            continue
        ts = int(o.get("T") or it.get("E"))
        out.append(_ev(ts, "binance", f'{o["s"]}-{ts}-{o["S"]}-{qty:g}', "long" if o["S"] == "SELL" else "short", px, qty))
    return out


def parse_bybit(msg: dict) -> list[dict]:
    """Messaggio allLiquidation.BTCUSDT → eventi. data[i]: T ms, s simbolo, S lato (Buy = long liquidato), v size BTC, p prezzo."""
    if not str(msg.get("topic", "")).startswith("allLiquidation."):
        return []
    out = []
    for d in msg.get("data") or []:
        if d.get("S") not in ("Buy", "Sell") or not d.get("s", "").startswith("BTC"):
            continue
        qty, px = float(d.get("v") or 0), float(d.get("p") or 0)
        if qty <= 0 or px <= 0:
            continue
        ts = int(d["T"])
        out.append(_ev(ts, "bybit", f'{d["s"]}-{ts}-{d["S"]}-{d["v"]}-{d["p"]}', "long" if d["S"] == "Buy" else "short", px, qty))
    return out


def parse_okx_ws(msg: dict) -> list[dict]:
    """Messaggio liquidation-orders → eventi BTC-USDT-SWAP (stesso parser e stessi id della raccolta REST)."""
    if (msg.get("arg") or {}).get("channel") != "liquidation-orders":
        return []
    out = []
    for d in msg.get("data") or []:
        if d.get("instId") == OKX_INST:
            out += parse_okx(d.get("details") or [])
    return out


PARSERS = {"binance": parse_binance, "bybit": parse_bybit, "okx": parse_okx_ws}


def parse(exchange: str, raw) -> list[dict]:
    """Testo grezzo dal socket → eventi; ignora pong, conferme di sottoscrizione e messaggi non validi."""
    if isinstance(raw, bytes):
        raw = raw.decode("utf-8", "replace")
    if not raw or raw in ("pong", "ping"):
        return []
    try:
        msg = json.loads(raw)
    except ValueError:
        return []
    try:
        return PARSERS[exchange](msg) if isinstance(msg, (dict, list)) else []
    except (KeyError, TypeError, ValueError) as e:
        log.warning("%s: messaggio non interpretato (%s): %.200s", exchange, type(e).__name__, raw)
        return []


# ------------------------------------------------------------------ archivio orario
def hour_key(ts_ms: int) -> str:
    return datetime.fromtimestamp(ts_ms / 1000, timezone.utc).strftime("%Y-%m-%d/%H")


def hour_path(root: Path, key: str) -> Path:
    return Path(root) / f"{key}.csv"


class Store:
    """Eventi in memoria divisi per ora UTC, senza doppioni; flush() scrive su disco le ore (fondendo con il file esistente)."""

    def __init__(self, root: Path):
        self.root = Path(root)
        self.hours: dict[str, dict[tuple, dict]] = {}
        self.stats: dict[str, dict] = {}

    def add(self, events: list[dict], exchange: str | None = None) -> int:
        n = 0
        for e in events:
            h = self.hours.setdefault(hour_key(e["ts"]), {})
            k = (e["exchange"], e["id"])
            if k not in h:
                h[k] = e
                n += 1
        if exchange:
            s = self.stats.setdefault(exchange, {"events": 0, "reconnects": 0, "last_msg": None, "last_event": None})
            s["events"] += n
            if events:
                s["last_event"] = max(e["ts"] for e in events)
        return n

    def seen(self, exchange: str) -> None:
        self.stats.setdefault(exchange, {"events": 0, "reconnects": 0, "last_msg": None, "last_event": None})["last_msg"] = int(time.time() * 1000)

    def flush(self, now_ms: int | None = None, closed_only: bool = True) -> list[Path]:
        """Scrive le ore chiuse (o tutte, alla chiusura del processo). Controllo di qualità con liqsources.check."""
        now_key = hour_key(now_ms or int(time.time() * 1000))
        written = []
        for key in sorted(self.hours):
            if closed_only and key >= now_key:
                continue
            p = hour_path(self.root, key)
            rows = dict(self.hours.pop(key))
            if p.exists():
                with open(p, newline="") as f:
                    for r in csv.DictReader(f):
                        r["ts"], r["price"], r["btc"], r["usd"] = int(r["ts"]), float(r["price"]), float(r["btc"]), float(r["usd"])
                        rows.setdefault((r["exchange"], r["id"]), r)
            good, notes = check(list(rows.values()), now_ms)
            for n in notes:
                log.warning("ora %s: %s", key, n)
            p.parent.mkdir(parents=True, exist_ok=True)
            tmp = p.with_suffix(".tmp")
            with open(tmp, "w", newline="") as f:
                w = csv.DictWriter(f, fieldnames=COLS, extrasaction="ignore")
                w.writeheader()
                w.writerows(sorted(good, key=lambda e: (e["ts"], e["exchange"], e["id"])))
            tmp.replace(p)
            written.append(p)
        return written

    def write_status(self) -> Path:
        p = self.root / "status.json"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(json.dumps({"ts": int(time.time() * 1000), "exchanges": self.stats}, indent=1))
        return p


# ------------------------------------------------------------------ git (credenziali solo da variabili d'ambiente)
def git_env(environ: dict | None = None) -> dict:
    """Ambiente per git: chiave di deploy (LIQSTREAM_SSH_KEY) o token (LIQSTREAM_GIT_TOKEN) come header http via GIT_CONFIG_*."""
    src = dict(os.environ if environ is None else environ)
    env = dict(src)
    env["GIT_TERMINAL_PROMPT"] = "0"
    key = src.get("LIQSTREAM_SSH_KEY")
    tok = src.get("LIQSTREAM_GIT_TOKEN")
    if key:
        env["GIT_SSH_COMMAND"] = f'ssh -i "{key}" -o IdentitiesOnly=yes -o StrictHostKeyChecking=accept-new'
    elif tok:
        basic = base64.b64encode(f"x-access-token:{tok}".encode()).decode()
        env.update(GIT_CONFIG_COUNT="1", GIT_CONFIG_KEY_0="http.https://github.com/.extraheader",
                   GIT_CONFIG_VALUE_0=f"AUTHORIZATION: basic {basic}")
    env.pop("LIQSTREAM_GIT_TOKEN", None)
    return env


def push_commands(subdir: str, branch: str, msg: str) -> list[list[str]]:
    return [["git", "add", "--", subdir],
            ["git", "-c", "user.name=liqstream-bot", "-c", "user.email=liqstream-bot@users.noreply.github.com",
             "commit", "-q", "-m", msg, "--", subdir],
            ["git", "pull", "-q", "--rebase", "origin", branch],
            ["git", "push", "-q", "origin", f"HEAD:{branch}"]]


def git_push(repo: Path, subdir: str = "data/liq_stream", branch: str | None = None, tries: int = 3) -> bool:
    """Commit e push dei soli file del raccoglitore. Errori nel log senza fermare la raccolta."""
    branch = branch or os.environ.get("LIQSTREAM_BRANCH", "claude/vibrant-brahmagupta-fvv2gh")
    env = git_env()

    def run(cmd):
        return subprocess.run(cmd, cwd=repo, env=env, capture_output=True, text=True, timeout=180)

    if not run(["git", "status", "--porcelain", "--", subdir]).stdout.strip():
        log.info("push: niente di nuovo")
        return True
    msg = f"liqstream: liquidazioni Binance/Bybit/OKX fino alle {datetime.now(timezone.utc):%Y-%m-%d %H:00} UTC"
    cmds = push_commands(subdir, branch, msg)
    for c in cmds[:2]:
        r = run(c)
        if r.returncode and "nothing to commit" not in (r.stdout + r.stderr):
            log.error("push: %s non riuscito: %s", c[1] if c[1] != "-c" else "commit", (r.stderr or r.stdout).strip()[:300])
            return False
    for i in range(1, tries + 1):
        ok = all(run(c).returncode == 0 for c in cmds[2:])
        if ok:
            log.info("push riuscito")
            return True
        run(["git", "rebase", "--abort"])
        log.warning("push non riuscito (tentativo %d/%d)", i, tries)
        time.sleep(10 * i)
    return False


# ------------------------------------------------------------------ socket (rete)
async def _app_ping(ws, every: float, payload: str):
    while True:
        await asyncio.sleep(every)
        await ws.send(payload)


async def stream(exchange: str, store: Store, stop: asyncio.Event):
    """Un exchange: connessione, sottoscrizione, lettura; riconnessione automatica con attesa crescente (1 s → 60 s)."""
    import websockets   # solo sulla VM: il tool e i test non ne hanno bisogno
    wait = 1.0
    while not stop.is_set():
        pinger = None
        try:
            async with websockets.connect(URLS[exchange], ping_interval=20, ping_timeout=30, close_timeout=5, max_size=2 ** 22) as ws:
                if exchange in SUBSCRIBE:
                    await ws.send(json.dumps(SUBSCRIBE[exchange]))
                if exchange in APP_PING:
                    pinger = asyncio.create_task(_app_ping(ws, *APP_PING[exchange]))
                log.info("%s: connesso", exchange)
                wait = 1.0
                async for raw in ws:
                    store.seen(exchange)
                    evs = parse(exchange, raw)
                    if evs:
                        store.add(evs, exchange)
                    if stop.is_set():
                        break
        except asyncio.CancelledError:
            raise
        except Exception as e:  # noqa: BLE001  (rete, chiusura del server ogni 24 h, 451/403 se la VM è in una regione bloccata)
            log.warning("%s: connessione persa (%s: %s), nuovo tentativo fra %.0f s", exchange, type(e).__name__, str(e)[:120], wait)
        finally:
            if pinger:
                pinger.cancel()
        if stop.is_set():
            break
        store.stats.setdefault(exchange, {"events": 0, "reconnects": 0, "last_msg": None, "last_event": None})["reconnects"] += 1
        await asyncio.sleep(wait + random.random())
        wait = min(wait * 2, 60.0)


async def hourly(store: Store, repo: Path, push: bool, stop: asyncio.Event, every: float = PUSH_EVERY_S):
    """Ogni ora (pochi secondi dopo hh:00): scrive le ore chiuse, lo stato, controlla i silenzi e spinge sul repo."""
    while not stop.is_set():
        now = time.time()
        delay = every - (now % every) + 20 if every == 3600 else every
        try:
            await asyncio.wait_for(stop.wait(), timeout=delay)
        except asyncio.TimeoutError:
            pass
        files = store.flush()
        store.write_status()
        now_ms = int(time.time() * 1000)
        for ex, s in store.stats.items():
            if not s.get("last_msg") or now_ms - s["last_msg"] > SILENCE_WARN_S * 1000:
                log.warning("%s: nessun messaggio da oltre %d ore", ex, SILENCE_WARN_S // 3600)
        log.info("ora chiusa: %d file; %s", len(files),
                 ", ".join(f"{k} {v['events']} eventi/{v['reconnects']} riconn." for k, v in store.stats.items()))
        if push and files:
            await asyncio.to_thread(git_push, repo)


async def main_async(repo: Path, exchanges: list[str], push: bool):
    store = Store(repo / "data" / "liq_stream")
    stop = asyncio.Event()
    loop = asyncio.get_running_loop()
    import signal
    for sig in (signal.SIGINT, signal.SIGTERM):
        try:
            loop.add_signal_handler(sig, stop.set)
        except NotImplementedError:
            pass
    tasks = [asyncio.create_task(stream(x, store, stop)) for x in exchanges]
    tasks.append(asyncio.create_task(hourly(store, repo, push, stop)))
    await stop.wait()
    log.info("chiusura: salvo anche l'ora in corso")
    for t in tasks:
        t.cancel()
    await asyncio.gather(*tasks, return_exceptions=True)
    store.flush(closed_only=False)
    store.write_status()


def main(argv=None):
    ap = argparse.ArgumentParser(description="Raccoglitore WebSocket delle liquidazioni BTC (Binance, Bybit, OKX)")
    ap.add_argument("--repo", default=str(Path(__file__).resolve().parent.parent), help="cartella del clone del repo")
    ap.add_argument("--exchanges", default="binance,bybit,okx")
    ap.add_argument("--no-push", action="store_true", help="solo file locali, niente git push")
    a = ap.parse_args(argv)
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s: %(message)s")
    ex = [x.strip() for x in a.exchanges.split(",") if x.strip() in URLS]
    log.info("avvio: %s, repo %s, push %s", ",".join(ex), a.repo, "no" if a.no_push else "sì")
    asyncio.run(main_async(Path(a.repo), ex, not a.no_push))


if __name__ == "__main__":
    main()
