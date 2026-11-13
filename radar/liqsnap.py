"""Registratore orario dei prezzi di liquidazione VERI delle posizioni BTC on-chain (Hyperliquid + Lighter).

Serve al test preregistrato in research/liq_onchain/PREREG.md ("i cluster reali di liquidazione delle balene attirano il prezzo /
fanno da supporto?"). Gira dentro radar/liqmap.update (ogni ora, in try/except): nessun blocco nuovo in cli.

Fonti (solo API pubbliche documentate, senza chiavi):
- Hyperliquid https://api.hyperliquid.xyz/info, clearinghouseState (peso 2; limite 1.200 di peso al minuto per IP: qui si sta
  sotto ~900/min e su 429 si aspetta e si riprova). Conti: wallet whalebot + 80 più grandi (letti ogni ora da liqmap) + TUTTI i conti
  della classifica con accountValue ≥ $1M, divisi in ROT_SLOTS gruppi fissi (hash dell'indirizzo) letti a rotazione: ogni conto
  ogni ROT_SLOTS ore; chi ha BTC per ≥ HOT_USD si rilegge ogni ora ("caldi").
- Lighter https://mainnet.zklighter.elliot.ai (docs.lighter.xyz): pnlLeaderboard ordinato per account_value (pubblico) → conti
  ≥ $1M; account?by=l1_address (snapshot pubblico: posizioni con liquidation_price). Limite conti standard: 60 richieste/min per IP,
  qui una ogni 1,1 s, in un thread parallelo a Hyperliquid.

Quando gira: dentro il giro completo del radar (daily.yml) E da solo (python -m radar.liqsnap) ogni ora in
.github/workflows/liqsnap.yml, perché il cron di GitHub fa partire daily.yml solo ogni 2–5 ore (causa delle fotografie rade
dell'11–13/11; la lettura in sé dura ~60 s). Una sola fotografia per ora (last_hour nello stato): chi arriva secondo non scrive.
Un solo scrittore: se la catena oraria ha aggiornato data/liqsnap/*_state.json da meno di 2 ore (chain_at), il giro completo
non legge né scrive nulla e riassume l'ultimo stato salvato (chain_alive, view). Allineamento con il remoto: sync_repo.
Ordine delle letture: conti prioritari (whalebot + primi 80 della classifica) e "caldi", poi la rotazione; oltre BUDGET_S
secondi le letture rimaste si saltano (la fotografia usa quelle fatte + le letture recenti).

Fra un giro e l'altro si tiene l'ultima lettura di ogni conto con BTC (data/liqsnap/*_state.json, al massimo MAX_AGE_H ore):
la fotografia oraria = letture fresche + letture recenti dei conti non toccati dalla rotazione (dichiarate in "cached").

Formato salvato (scelta per tenere il repo piccolo): NON una riga per posizione (~400 posizioni/ora ≈ 5 MB/mese compressi) ma
fasce già aggregate. data/liqsnap/{hl,lighter}_YYYY-MM.csv.gz, colonne ts, mid, k, long_usd, short_usd, n_long, n_short:
fascia k = prezzi di liquidazione in [mid·(1+k·0,25%), mid·(1+(k+1)·0,25%)), k da −60 a 59 (±15%), solo fasce non vuote.
Ogni ora si AGGIUNGE un membro gzip in coda (il file non si riscrive: i delta git restano piccoli). Una riga di copertura per giro
in data/liqsnap/coverage_YYYY-MM.csv (conti letti, nozionale BTC, posizioni scartate e perché, fuori fascia, secondi).
"""
from __future__ import annotations

import csv
import gzip
import hashlib
import io
import json
import math
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path

import requests

HL_API = "https://api.hyperliquid.xyz/info"
LT_API = "https://mainnet.zklighter.elliot.ai/api/v1"
STEP = 0.0025          # fasce dello 0,25%
RNG = 0.15             # ±15% dal prezzo
KMIN, KMAX = -int(round(RNG / STEP)), int(round(RNG / STEP)) - 1   # −60 … 59
MIN_ACCOUNT_USD = 1e6  # conti della classifica da coprire
ROT_SLOTS = 6          # ogni conto almeno ogni 6 ore
HOT_USD = 1e6          # posizioni BTC ≥ $1M: si rileggono ogni ora
HOT_MAX = {"hl": 150, "lighter": 25}
MAX_AGE_H = 6.5        # letture più vecchie: scartate (dati vecchi)
FRESH_S = 900          # una lettura Hyperliquid con "time" più vecchio di 15 minuti è considerata vecchia
HL_RATE = 7.0          # richieste/s verso Hyperliquid (peso 2 → ~840/min, sotto il limite di 1.200)
LT_GAP = 1.1           # secondi fra due richieste Lighter (60/min)
BUDGET_S = 300.0       # tempo massimo delle letture per giro (daily.yml ha 20 minuti in tutto; un giro tipico ne usa ~60 s)
CLUSTER_MIN_USD = 2e6  # cluster: almeno $2M su 3 fasce …
CLUSTER_REL = 0.20     # … e almeno il 20% del più grande dello stesso lato entro ±15%
COV_FIELDS = ["ts", "ex", "mid", "oi_usd", "target", "read", "failed", "http_429", "cached", "holders", "positions", "ntl_long", "ntl_short",
              "binned_long", "binned_short", "beyond_long", "beyond_short", "no_liq_usd", "wrong_side", "stale", "dupes", "secs"]


# ------------------------------------------------------------------ funzioni pure (tests/test_liqsnap.py)
def _f(x) -> float:
    try:
        v = float(x)
        return v if math.isfinite(v) else 0.0
    except (TypeError, ValueError):
        return 0.0


def parse_hl(state: dict, addr: str, coin: str = "BTC") -> list[dict]:
    """Posizioni BTC (DEX principale) da un clearinghouseState di Hyperliquid."""
    ts = _f((state or {}).get("time")) / 1000 or None
    out = []
    for ap in (state or {}).get("assetPositions", []) or []:
        p = ap.get("position") or {}
        if p.get("coin") != coin:
            continue
        sz = _f(p.get("szi"))
        if not sz:
            continue
        liq = _f(p.get("liquidationPx")) or None
        out.append({"ex": "hl", "acct": addr.lower(), "side": "long" if sz > 0 else "short", "btc": abs(sz),
                    "entry": _f(p.get("entryPx")), "liq": liq, "lev": _f((p.get("leverage") or {}).get("value")) or None,
                    "ntl": _f(p.get("positionValue")) or None, "ts": ts})
    return out


def parse_lighter(resp: dict, ts: float, symbol: str = "BTC") -> list[dict]:
    """Posizioni BTC da account?by=l1_address di Lighter (tutti i sotto-conti). liquidation_price 0 = nessuna liquidazione."""
    out = []
    for a in (resp or {}).get("accounts", []) or []:
        for p in a.get("positions", []) or []:
            if p.get("symbol") != symbol:
                continue
            sz = _f(p.get("position")) * (1 if int(_f(p.get("sign")) or 1) > 0 else -1)
            if not sz:
                continue
            imf = _f(p.get("initial_margin_fraction"))
            out.append({"ex": "lighter", "acct": str(a.get("index", a.get("account_index"))), "side": "long" if sz > 0 else "short",
                        "btc": abs(sz), "entry": _f(p.get("avg_entry_price")), "liq": _f(p.get("liquidation_price")) or None,
                        "lev": round(100 / imf, 1) if imf > 0 else None, "ntl": _f(p.get("position_value")) or None, "ts": ts})
    return out


def check(pos: dict, mid: float) -> str | None:
    """Motivo per scartare una posizione dal binning (None = buona). 'no_liq' = nessun prezzo di liquidazione (conto molto
    capiente): si conta nel nozionale ma non entra nelle fasce. 'wrong_side' = liquidazione dal lato sbagliato del prezzo
    (long con liq ≥ prezzo, short con liq ≤ prezzo): dato incoerente o posizione già liquidata dopo la lettura."""
    if not pos.get("btc") or pos["btc"] <= 0 or not mid or mid <= 0:
        return "bad"
    liq = pos.get("liq")
    if not liq or liq <= 0:
        return "no_liq"
    if (pos["side"] == "long" and liq >= mid) or (pos["side"] == "short" and liq <= mid):
        return "wrong_side"
    return None


def dedupe(positions: list[dict]) -> tuple[list[dict], int]:
    """Una sola posizione per (exchange, conto, lato): si tiene la lettura più recente. Ritorna (posizioni, doppioni tolti)."""
    best: dict = {}
    for p in positions:
        k = (p["ex"], p["acct"], p["side"])
        if k not in best or (p.get("ts") or 0) > (best[k].get("ts") or 0):
            best[k] = p
    return list(best.values()), len(positions) - len(best)


def bin_index(liq: float, mid: float, step: float = STEP) -> int:
    return int(math.floor((liq / mid - 1) / step + 1e-9))


def bins(positions: list[dict], mid: float, step: float = STEP) -> tuple[dict[int, list], dict]:
    """Aggrega le posizioni buone in fasce di prezzo di liquidazione relative al prezzo: {k: [long_usd, short_usd, n_long, n_short]}.
    Il $ è size × prezzo attuale. Fuori da ±15% va in beyond_long/beyond_short. Ritorna (fasce, conteggi)."""
    out: dict[int, list] = {}
    st = {"positions": 0, "ntl_long": 0.0, "ntl_short": 0.0, "binned_long": 0.0, "binned_short": 0.0, "beyond_long": 0.0,
          "beyond_short": 0.0, "no_liq_usd": 0.0, "wrong_side": 0, "bad": 0}
    for p in positions:
        usd = p["btc"] * mid
        why = check(p, mid)
        if why == "bad":
            st["bad"] += 1
            continue
        st["positions"] += 1
        st["ntl_" + p["side"]] += usd
        if why == "no_liq":
            st["no_liq_usd"] += usd
            continue
        if why == "wrong_side":
            st["wrong_side"] += 1
            continue
        k = bin_index(p["liq"], mid, step)
        if not KMIN <= k <= KMAX:
            st["beyond_" + p["side"]] += usd
            continue
        b = out.setdefault(k, [0.0, 0.0, 0, 0])
        j = 0 if p["side"] == "long" else 1
        b[j] += usd
        b[2 + j] += 1
        st["binned_" + p["side"]] += usd
    return out, st


def clusters(b: dict[int, list], mid: float, side: str, step: float = STEP, min_usd: float = CLUSTER_MIN_USD,
             rel: float = CLUSTER_REL) -> list[dict]:
    """Cluster reali di un lato ("long" sotto il prezzo, "short" sopra): picchi della somma su 3 fasce adiacenti,
    significativi se ≥ min_usd e ≥ rel × il picco più grande del lato. Dal più vicino al più lontano."""
    j = 0 if side == "long" else 1
    ks = range(KMIN, 0) if side == "long" else range(0, KMAX + 1)
    v = {k: (b.get(k) or [0, 0, 0, 0])[j] for k in ks}
    n = {k: (b.get(k) or [0, 0, 0, 0])[2 + j] for k in ks}
    band = {k: v.get(k - 1, 0) + v[k] + v.get(k + 1, 0) for k in ks}
    key = {k: (band[k], v[k]) for k in ks}   # a pari somma vince la fascia più piena: il cluster resta centrato sul livello vero
    peaks = [k for k in ks if band[k] > 0 and key[k] >= key.get(k - 1, (0, 0)) and key[k] > key.get(k + 1, (0, 0))]
    if not peaks:
        return []
    top = max(band[k] for k in peaks)
    out = []
    for k in peaks:
        if band[k] >= min_usd and band[k] >= rel * top:
            px = mid * (1 + (k + 0.5) * step)
            out.append({"k": k, "price": round(px, 0), "usd": round(band[k], 0), "dist_pct": round((px / mid - 1) * 100, 2),
                        "n": int(n.get(k - 1, 0) + n[k] + n.get(k + 1, 0)), "rel": round(band[k] / top, 2)})
    return sorted(out, key=lambda c: abs(c["dist_pct"]))


def rotation(addrs: list[str], hour: int, slots: int = ROT_SLOTS) -> list[str]:
    """Gruppo della rotazione per quest'ora: ogni indirizzo ha un gruppo fisso (hash), letto ogni `slots` ore."""
    s = hour % slots
    return [a for a in addrs if int(hashlib.sha1(a.lower().encode()).hexdigest()[:8], 16) % slots == s]


def merge_state(state: dict, fresh: dict[str, list], now: float, max_age_h: float = MAX_AGE_H) -> tuple[dict, int]:
    """Stato {conto: {"t": secondi, "p": [posizioni]}}: le letture fresche sostituiscono le vecchie (anche "nessuna posizione"
    BTC → il conto esce); quelle più vecchie di max_age_h si scartano. Ritorna (stato nuovo, letture scartate perché vecchie)."""
    out, stale = {}, 0
    for a, v in (state or {}).items():
        if a in fresh:
            continue
        if now - (v.get("t") or 0) > max_age_h * 3600:
            stale += 1
            continue
        out[a] = v
    for a, ps in fresh.items():
        if ps:
            out[a] = {"t": now, "p": ps}
    return out, stale


def hot(state: dict, mid: float, min_usd: float = HOT_USD, cap: int = 150, near: float = 0.20) -> list[str]:
    """Conti con posizioni BTC grandi (≥ min_usd) e liquidazione entro ±near dal prezzo (quelle che spostano le fasce),
    dall'ultima lettura: si rileggono ogni ora, dai più grandi."""
    size = {a: sum(p["btc"] for p in v.get("p", []) if p.get("liq") and abs(p["liq"] / mid - 1) <= near) * mid
            for a, v in (state or {}).items()}
    return [a for a, u in sorted(size.items(), key=lambda x: -x[1]) if u >= min_usd][:cap]


def snapshot_rows(ts: str, mid: float, b: dict[int, list]) -> list[list]:
    return [[ts, round(mid, 1), k, round(v[0]), round(v[1]), v[2], v[3]] for k, v in sorted(b.items())]


def append_gz(path: Path, rows: list[list], header: list[str]) -> int:
    """Aggiunge le righe come nuovo membro gzip in coda (mtime fisso); l'intestazione solo se il file non esiste."""
    buf = io.StringIO()
    w = csv.writer(buf, lineterminator="\n")
    if not path.exists():
        w.writerow(header)
    w.writerows(rows)
    data = gzip.compress(buf.getvalue().encode(), compresslevel=9, mtime=0)
    with open(path, "ab") as fh:
        fh.write(data)
    return len(data)


def summary(b: dict[int, list], mid: float) -> dict:
    up, dn = clusters(b, mid, "short"), clusters(b, mid, "long")
    return {"nearest_above": up[0] if up else None, "nearest_below": dn[0] if dn else None,
            "largest_above": max(up, key=lambda c: c["usd"], default=None), "largest_below": max(dn, key=lambda c: c["usd"], default=None),
            "above": up[:6], "below": dn[:6]}


# ------------------------------------------------------------------ rete
class _Limiter:
    def __init__(self, per_s: float):
        self.gap, self.next, self.lock = 1.0 / per_s, 0.0, threading.Lock()

    def wait(self):
        with self.lock:
            t = time.monotonic()
            if t < self.next:
                time.sleep(self.next - t)
            self.next = max(t, self.next) + self.gap


class _HL:
    """clearinghouseState con limite di frequenza e attesa su 429 (2, 4, 8 s); dopo troppi 429 o oltre la scadenza
    (budget del giro) si smette: giro parziale, le letture mancanti contano come fallite."""
    def __init__(self, session=None, per_s: float = HL_RATE, deadline: float | None = None):
        self.s, self.lim, self.n429, self.stop = session or requests.Session(), _Limiter(per_s), 0, False
        self.deadline = deadline

    def post(self, body: dict):
        for back in (2, 4, 8, None):
            if self.stop or (self.deadline and time.monotonic() > self.deadline):
                return None
            self.lim.wait()
            r = self.s.post(HL_API, json=body, timeout=20)
            if r.status_code == 429:
                self.n429 += 1
                if self.n429 >= 10:
                    self.stop = True
                if back is None:
                    return None
                time.sleep(back)
                continue
            r.raise_for_status()
            return r.json()
        return None

    def states(self, addrs: list[str]) -> tuple[dict, int]:
        def one(a):
            try:
                return a, self.post({"type": "clearinghouseState", "user": a})
            except Exception:  # noqa: BLE001
                return a, None
        with ThreadPoolExecutor(6) as ex:
            res = list(ex.map(one, addrs))
        ok = {a: s for a, s in res if s}
        return ok, len(addrs) - len(ok)


def _load(path: Path) -> dict:
    try:
        return json.loads(path.read_text()) if path.exists() else {}
    except Exception:  # noqa: BLE001
        return {}


def _save_state(path: Path, d: dict):
    """Un conto per riga: file leggibile e delta git piccoli."""
    acc = d.get("acc", {})
    head = {k: v for k, v in d.items() if k != "acc"}
    lines = [json.dumps(head)[:-1] + ', "acc": {']
    items = [f"{json.dumps(a)}: {json.dumps(v, separators=(',', ':'))}" for a, v in sorted(acc.items())]
    lines.append(",\n".join(items))
    lines.append("}}")
    path.write_text("\n".join(lines) + "\n")


def _compact(ps: list[dict]) -> list[dict]:
    return [{"side": p["side"], "btc": round(p["btc"], 5), "entry": round(p["entry"], 1), "liq": round(p["liq"], 1) if p.get("liq") else None,
             "lev": p.get("lev"), "ts": round(p["ts"]) if p.get("ts") else None, "acct": p["acct"], "ex": p["ex"]} for p in ps]


def _record(ex: str, d: Path, ts: str, now: float, mid: float, fresh: dict[str, list], target: int, failed: int, n429: int,
            stale_reads: int, t0: float, write: bool, oi_usd: float | None = None, chain: bool = False) -> dict:
    """Unisce letture fresche e stato, controlla, aggrega, scrive fotografia + copertura, logga. Ritorna il riassunto."""
    sp = d / f"{ex}_state.json"
    st = _load(sp)
    acc, stale = merge_state(st.get("acc", {}), {a: _compact(v) for a, v in fresh.items()}, now)
    allp = [p for v in acc.values() for p in v["p"]]
    allp, dupes = dedupe(allp)
    b, c = bins(allp, mid)
    cached = sum(1 for a in acc if a not in fresh)
    cov = {"ts": ts, "ex": ex, "mid": round(mid, 1), "oi_usd": round(oi_usd) if oi_usd else None, "target": target, "read": target - failed, "failed": failed, "http_429": n429,
           "cached": cached, "holders": len(acc), "positions": c["positions"], **{k: round(c[k]) for k in
           ("ntl_long", "ntl_short", "binned_long", "binned_short", "beyond_long", "beyond_short", "no_liq_usd")},
           "wrong_side": c["wrong_side"], "stale": stale + stale_reads, "dupes": dupes, "secs": round(time.time() - t0, 1)}
    print(f"[liqsnap] {ex}: conti letti {cov['read']}/{target} (falliti {failed}, 429: {n429}), con BTC {len(acc)} "
          f"({len(acc) - cached} freschi, {cached} da letture ≤ {MAX_AGE_H} h); nozionale BTC long ${c['ntl_long'] / 1e6:,.0f}M "
          f"short ${c['ntl_short'] / 1e6:,.0f}M; in fascia ±15% long ${c['binned_long'] / 1e6:,.0f}M short ${c['binned_short'] / 1e6:,.0f}M; "
          f"senza liq ${c['no_liq_usd'] / 1e6:,.0f}M; scartate: lato sbagliato {c['wrong_side']}, vecchie {stale + stale_reads}, doppioni {dupes}; "
          f"{cov['secs']} s" + (f"; copertura dell'OI BTC dell'exchange (${oi_usd / 1e6:,.0f}M per lato): long "
                                f"{c['ntl_long'] / oi_usd:.0%}, short {c['ntl_short'] / oi_usd:.0%}" if oi_usd else ""))
    if target and failed > target / 2:
        print(f"[liqsnap] {ex}: più di metà delle letture fallite: fotografia parziale")
    wrote = False
    if write and target - failed > 0 and c["positions"] > 0:
        m = ts[:7]
        append_gz(d / f"{ex}_{m}.csv.gz", snapshot_rows(ts, mid, b), ["ts", "mid", "k", "long_usd", "short_usd", "n_long", "n_short"])
        cf = d / f"coverage_{m}.csv"
        new = not cf.exists()
        with open(cf, "a", newline="") as fh:
            w = csv.DictWriter(fh, COV_FIELDS, lineterminator="\n")
            if new:
                w.writeheader()
            w.writerow(cov)
        wrote = True
    elif write:
        print(f"[liqsnap] {ex}: nessuna lettura valida, fotografia non scritta (nessun dato inventato)")
    st.update(acc=acc, mid=round(mid, 1))
    if chain:   # giro della catena oraria (liqsnap.yml): finché è recente, il giro completo non scrive (un solo scrittore)
        st["chain_at"] = int(now)
    if wrote:
        st["last_hour"] = ts[:13]
    _save_state(sp, st)
    return {"bins": b, "cov": cov, "wrote": wrote}


def _lt_get(s, path, params, last=[0.0]):  # noqa: B006 (pausa condivisa fra le chiamate)
    for back in (5, 15, None):
        dt = LT_GAP - (time.monotonic() - last[0])
        if dt > 0:
            time.sleep(dt)
        last[0] = time.monotonic()
        r = s.get(f"{LT_API}/{path}", params=params, timeout=20)
        if r.status_code == 429 and back:
            time.sleep(back)
            continue
        r.raise_for_status()
        return r.json()
    return None


def lighter_accounts(d: Path, s, max_age_h: float = 24) -> list[str]:
    """Indirizzi L1 dei conti Lighter con account_value ≥ $1M (pnlLeaderboard pubblico), cache giornaliera."""
    cp = d / "lighter_accounts.json"
    c = _load(cp)
    if not c.get("ts") or time.time() - c["ts"] > max_age_h * 3600:
        rows, off = [], 0
        while off < 1000:
            e = (_lt_get(s, "pnlLeaderboard", {"time_window": "all", "sort_by": "account_value", "sort_dir": "desc", "limit": 100,
                                               "offset": off}) or {}).get("entries") or []
            rows += e
            if len(e) < 100 or float(e[-1].get("account_value") or 0) < MIN_ACCOUNT_USD:
                break
            off += 100
        addrs = list(dict.fromkeys(r["l1_address"].lower() for r in rows if float(r.get("account_value") or 0) >= MIN_ACCOUNT_USD))
        if addrs:
            c = {"ts": time.time(), "accounts": addrs}
            cp.write_text(json.dumps(c, indent=0))
    return c.get("accounts", [])


def todo_list(prio: list[str], hot_: list[str], rot: list[str], skip=()) -> list[str]:
    """Ordine delle letture: prima i conti prioritari (più grandi) e i "caldi", poi la rotazione; senza doppioni.
    Con il budget del giro a rischio si perdono solo le ultime letture della rotazione (restano le letture ≤ MAX_AGE_H)."""
    skip = {a.lower() for a in skip}
    return [a for a in dict.fromkeys(x.lower() for x in list(prio) + list(hot_) + list(rot)) if a not in skip]


def run_lighter(d: Path, ts: str, hour: int, mid: float, write: bool, deadline: float | None = None, chain: bool = False) -> dict:
    t0, now, s = time.time(), time.time(), requests.Session()
    addrs = lighter_accounts(d, s)
    st = _load(d / "lighter_state.json")
    # nello stato le chiavi sono indirizzi L1 (un indirizzo = tutti i suoi sotto-conti)
    todo = list(dict.fromkeys(hot(st.get("acc", {}), mid, cap=HOT_MAX["lighter"]) + (rotation(addrs, hour) if write else [])))
    fresh, failed, n429, oi = {}, 0, 0, None
    try:   # open interest BTC di Lighter (mercato 1): misura della copertura
        o = ((_lt_get(s, "orderBookDetails", {"market_id": 1}) or {}).get("order_book_details") or [{}])[0]
        oi = _f(o.get("open_interest")) * mid if o.get("symbol", "BTC") == "BTC" else None
    except Exception:  # noqa: BLE001
        pass
    for a in todo:
        if deadline and time.monotonic() > deadline:
            failed += 1
            continue
        try:
            r = _lt_get(s, "account", {"by": "l1_address", "value": a, "active_only": "true"})
            if r is None:
                failed += 1; n429 += 1
                continue
            fresh[a] = parse_lighter(r, time.time())
        except Exception:  # noqa: BLE001
            failed += 1
    return _record("lighter", d, ts, now, mid, fresh, len(todo), failed, n429, 0, t0, write, oi, chain)


def run_hl(d: Path, ts: str, hour: int, mid: float, write: bool, big: list[str], base_states: dict | None, hl: _HL,
           oi: float | None = None, prio: list[str] | None = None, chain: bool = False) -> dict:
    t0, now = time.time(), time.time()
    st = _load(d / "hl_state.json")
    base_states = {a.lower(): v for a, v in (base_states or {}).items()}
    todo = todo_list(prio or [], hot(st.get("acc", {}), mid, cap=HOT_MAX["hl"]), rotation(big, hour) if write else [], base_states)
    got, failed = hl.states(todo)
    states = {**base_states, **{a.lower(): v for a, v in got.items()}}
    fresh, stale_reads = {}, 0
    for a, s in states.items():
        t = _f((s or {}).get("time")) / 1000
        if not t or now - t > FRESH_S:
            stale_reads += 1
            continue
        fresh[a] = parse_hl(s, a)
    target = len(todo) + len(base_states)
    return _record("hl", d, ts, now, mid, fresh, target, failed, hl.n429, stale_reads, t0, write, oi, chain)


CHAIN_ALIVE_H = 2.0    # la catena oraria (liqsnap.yml) è "viva" se ha aggiornato uno stato da meno di 2 ore


def chain_alive(d: Path, now: float | None = None, max_h: float = CHAIN_ALIVE_H) -> bool:
    """True se la catena oraria ha salvato uno stato (chain_at in data/liqsnap/*_state.json) da meno di max_h ore.
    Si usa il campo nel file e non la data di modifica: il checkout di git la reimposta a ogni giro."""
    now = time.time() if now is None else now
    ts = [_f(_load(Path(d) / f"{ex}_state.json").get("chain_at")) for ex in ("hl", "lighter")]
    return any(0 <= now - t < max_h * 3600 for t in ts if t)


def view(d: Path, ref_price: float | None = None) -> dict:
    """Riassunto in sola lettura dell'ultimo stato salvato dalla catena (nessuna rete, nessun file scritto)."""
    now, out, comb = time.time(), {"source": "catena oraria liqsnap.yml (sola lettura)", "bin_pct": STEP * 100, "range_pct": RNG * 100}, {}
    for ex in ("hl", "lighter"):
        st = _load(Path(d) / f"{ex}_state.json")
        mid = _f(ref_price) or _f(st.get("mid"))
        if not mid:
            out[ex] = {"ok": False}
            continue
        acc, _ = merge_state(st.get("acc", {}), {}, now)
        b, c = bins(dedupe([p for v in acc.values() for p in v["p"]])[0], mid)
        out[ex] = {"ok": True, "recorded": False, "last_hour": st.get("last_hour"), "holders": len(acc), "positions": c["positions"],
                   **summary(b, mid)}
        for k, v in b.items():
            cc = comb.setdefault(k, [0.0, 0.0, 0, 0])
            for i in range(4):
                cc[i] += v[i]
        out.setdefault("mid", round(mid, 1))
    print(f"[liqsnap] catena oraria attiva (stato < {CHAIN_ALIVE_H:g} h): il giro completo non scrive data/liqsnap, "
          f"riassunto dell'ultimo stato (ore {[(out.get(ex) or {}).get('last_hour') for ex in ('hl', 'lighter')]})")
    if "mid" in out:
        out.update(summary(comb, out["mid"]))
        out["bins"] = [[k, round(v[0]), round(v[1]), v[2] + v[3]] for k, v in sorted(comb.items())]
    out["ts"] = time.strftime("%Y-%m-%dT%H:%M", time.gmtime(now))
    return out


def record(data_dir, base_states: dict | None, big: list[str], ref_price: float | None = None, prio: list[str] | None = None,
           budget_s: float = BUDGET_S, chain: bool = False) -> dict:
    """Giro orario: Hyperliquid (con gli stati già letti da liqmap) e Lighter in parallelo. Ritorna report["liqmap"]["onchain"].
    `prio`: conti da leggere per primi (whalebot + più grandi della classifica, quando liqmap non li ha già letti).
    `budget_s`: oltre questo tempo le letture rimaste si saltano (fotografia con le letture fatte + quelle recenti).
    `chain`: True solo nel giro autonomo di liqsnap.yml. Nel giro completo (daily.yml, chain=False) con la catena viva
    (chain_alive) non si legge né si scrive nulla: si riassume l'ultimo stato salvato dalla catena (un solo scrittore)."""
    d = Path(data_dir) / "liqsnap"
    d.mkdir(parents=True, exist_ok=True)
    if not chain and chain_alive(d):
        return view(d, ref_price)
    deadline = time.monotonic() + budget_s
    hl = _HL(deadline=deadline)
    mid, hl_oi = 0.0, None
    try:   # prezzo medio e open interest BTC di Hyperliquid in una chiamata (peso 20)
        meta, ctx = hl.post({"type": "metaAndAssetCtxs"}) or ({}, [])
        i = [u.get("name") for u in meta.get("universe", [])].index("BTC")
        mid = _f(ctx[i].get("midPx")) or _f(ctx[i].get("markPx"))
        hl_oi = _f(ctx[i].get("openInterest")) * mid or None
    except Exception as e:  # noqa: BLE001
        print(f"[liqsnap] prezzo medio Hyperliquid non letto: {e!r}")
    if not mid:   # riserva: chiusura dell'ultima ora usata dalla mappa stimata
        mid = _f(ref_price)
        if not mid:
            raise RuntimeError("nessun prezzo BTC per la fotografia")
        print("[liqsnap] uso il prezzo della mappa stimata come riferimento")
    elif ref_price and abs(mid / ref_price - 1) > 0.03:
        print(f"[liqsnap] prezzo Hyperliquid {mid:,.0f} lontano dalla mappa ({ref_price:,.0f}): controllare le fonti")
    t = time.gmtime()
    ts, hour = time.strftime("%Y-%m-%dT%H:%M", t), int(time.time() // 3600)
    out = {"ts": ts, "mid": round(mid, 1), "bin_pct": STEP * 100, "range_pct": RNG * 100}
    res = {}

    def one(ex):
        try:
            write = _load(d / f"{ex}_state.json").get("last_hour") != ts[:13]   # una sola fotografia per ora (giro di riserva :37)
            if ex == "hl":
                return ex, run_hl(d, ts, hour, mid, write, big, base_states, hl, hl_oi, prio, chain)
            return ex, run_lighter(d, ts, hour, mid, write, deadline, chain)
        except Exception as e:  # noqa: BLE001
            print(f"[liqsnap] {ex} non disponibile: {e!r}")
            return ex, None
    with ThreadPoolExecutor(2) as ex:
        for k, r in ex.map(one, ("hl", "lighter")):
            res[k] = r
    comb: dict[int, list] = {}
    for k, r in res.items():
        out[k] = {"ok": r is not None, **({"coverage": r["cov"], "recorded": r["wrote"], **summary(r["bins"], mid)} if r else {})}
        for kk, v in (r or {}).get("bins", {}).items():
            c = comb.setdefault(kk, [0.0, 0.0, 0, 0])
            for i in range(4):
                c[i] += v[i]
    out.update(summary(comb, mid))
    out["bins"] = [[k, round(v[0]), round(v[1]), v[2] + v[3]] for k, v in sorted(comb.items())]
    return out


# ------------------------------------------------------------------ giro autonomo (.github/workflows/liqsnap.yml)
def done_this_hour(d: Path, hour: str) -> bool:
    """True se entrambe le borse hanno già la fotografia di quest'ora ("YYYY-MM-DDTHH")."""
    return all(_load(Path(d) / f"{ex}_state.json").get("last_hour") == hour for ex in ("hl", "lighter"))


def main() -> int:
    """Fotografia oraria senza il giro completo del radar (python -m radar.liqsnap). Il workflow orario di GitHub parte solo
    ogni 2–5 ore (cron best-effort): questo comando, chiamato ogni ora da liqsnap.yml, tiene la serie davvero oraria.
    Legge per primi i conti più grandi (whalebot + i primi 80 della classifica Hyperliquid) e i "caldi", poi la rotazione."""
    from . import liqmap
    from .data import DATA_DIR
    d = DATA_DIR / "liqsnap"
    hour = time.strftime("%Y-%m-%dT%H", time.gmtime())
    if done_this_hour(d, hour):
        print(f"[liqsnap] fotografia delle {hour}:00 già salvata (giro completo del radar): niente da fare")
        for ex in ("hl", "lighter"):   # la catena riprende il ruolo di unico scrittore dal giro successivo
            sp = d / f"{ex}_state.json"
            st = _load(sp)
            if st:
                st["chain_at"] = int(time.time())
                _save_state(sp, st)
        return 0
    names = liqmap.hl_accounts(DATA_DIR / "hl_accounts.json")   # cache giornaliera; classifica riletta solo se scaduta
    out = record(DATA_DIR, None, liqmap.hl_big(DATA_DIR / "hl_accounts.json"), None, prio=list(names), chain=True)
    rec = [ex for ex in ("hl", "lighter") if (out.get(ex) or {}).get("recorded")]
    print(f"[liqsnap] giro autonomo {out['ts']}: fotografie salvate {rec or 'nessuna'}")
    return 0


# ------------------------------------------------------------------ allineamento con il repository remoto (workflow)
# `git pull --rebase -X theirs` su file binari (i .csv.gz a membri accodati) teneva una sola versione intera e perdeva in silenzio
# i membri accodati dall'altro scrittore. Qui ogni file cambiato da entrambe le parti si unisce in modo esplicito:
# file in sola aggiunta (.csv.gz, .csv) = versione remota + byte aggiunti da noi; altri file (stati JSON) = la nostra versione,
# con una riga di log. Si usa in liqsnap.yml e daily.yml: python -m radar.liqsnap sync, poi git push.
APPEND_SUFFIXES = (".csv.gz", ".csv")


def _strip_header_gz(data: bytes) -> bytes:
    """Byte gzip senza la prima riga (intestazione), ricompressi in un solo membro."""
    txt = gzip.decompress(data).decode()
    return gzip.compress(txt.split("\n", 1)[1].encode() if "\n" in txt else b"", compresslevel=9, mtime=0)


def merge_file(path: str, base: bytes | None, mine: bytes | None, theirs: bytes | None) -> tuple[bytes | None, str]:
    """Unione a tre vie di un file (None = assente). Ritorna (contenuto, nota); contenuto None = file da cancellare."""
    if mine == theirs or theirs == base:
        return mine, "nostra"
    if mine == base:
        return theirs, "remota"
    if path.endswith(APPEND_SUFFIXES) and mine is not None and theirs is not None:
        b = base or b""
        if mine.startswith(b) and theirs.startswith(b):
            add = mine[len(b):]
            if base is None:   # file nuovo creato da entrambi (es. primo giro del mese): una sola intestazione
                if path.endswith(".gz"):
                    try:
                        add = _strip_header_gz(add)
                    except Exception:  # noqa: BLE001
                        return mine, "ATTENZIONE: gzip illeggibile, tenuta la nostra versione"
                else:
                    add = add.split(b"\n", 1)[1] if b"\n" in add else b""
            if path.endswith(".csv") and theirs and not theirs.endswith(b"\n"):
                theirs += b"\n"
            return theirs + add, "unita (remota + righe nostre)"
    if mine is None:
        return theirs, "remota (cancellata solo da noi)"
    return mine, "ATTENZIONE: cambiata da entrambi, tenuta la nostra versione"


def _git(repo, *args, check=True) -> str:
    import subprocess
    r = subprocess.run(["git", *args], cwd=repo, capture_output=True, check=False)
    if check and r.returncode:
        raise RuntimeError(f"git {' '.join(args)}: {r.stderr.decode(errors='replace').strip()}")
    return r.stdout.decode(errors="replace").strip() if r.returncode == 0 else ""


def _blob(repo, rev: str, path: str) -> bytes | None:
    import subprocess
    r = subprocess.run(["git", "cat-file", "blob", f"{rev}:{path}"], cwd=repo, capture_output=True, check=False)
    return r.stdout if r.returncode == 0 else None


def sync_repo(repo=".", remote: str = "origin", branch: str | None = None) -> str:
    """Porta il ramo locale sopra quello remoto senza perdere dati di nessuno dei due. Ritorna "ff", "ahead", "same" o "merged".
    I commit locali non ancora spinti si ricostruiscono in un solo commit sopra il remoto (file per file con merge_file)."""
    branch = branch or _git(repo, "rev-parse", "--abbrev-ref", "HEAD")
    _git(repo, "fetch", "-q", remote, branch)
    up = _git(repo, "rev-parse", "FETCH_HEAD")
    head = _git(repo, "rev-parse", "HEAD")
    if head == up:
        return "same"
    base = _git(repo, "merge-base", "HEAD", up, check=False)
    if base == head:
        _git(repo, "merge", "-q", "--ff-only", up)
        return "ff"
    if base == up:
        return "ahead"
    msg = _git(repo, "log", "-1", "--format=%B", "HEAD")
    files = [f for f in _git(repo, "diff", "--name-only", "--no-renames", base, "HEAD").splitlines() if f]
    out = {}
    for f in files:
        content, note = merge_file(f, _blob(repo, base, f) if base else None, _blob(repo, "HEAD", f), _blob(repo, up, f))
        out[f] = content
        print(f"[sync] {f}: {note}")
    dirty = bool(_git(repo, "status", "--porcelain", "--untracked-files=no"))
    if dirty:   # modifiche non salvate in un commit: messe da parte e riapplicate dopo (reset --hard le cancellerebbe)
        _git(repo, "stash", "push", "-q")
    _git(repo, "reset", "-q", "--hard", up)
    root = Path(_git(repo, "rev-parse", "--show-toplevel"))
    for f, content in out.items():
        fp = root / f
        if content is None:
            if fp.exists():
                fp.unlink()
            _git(repo, "rm", "-q", "--cached", "--ignore-unmatch", f)
            continue
        fp.parent.mkdir(parents=True, exist_ok=True)
        fp.write_bytes(content)
        _git(repo, "add", f)
    if _git(repo, "diff", "--cached", "--name-only"):
        _git(repo, "commit", "-q", "-m", msg or "data: aggiornamento")
    if dirty:
        try:
            _git(repo, "stash", "pop", "-q")
        except RuntimeError as e:
            print(f"[sync] ATTENZIONE: modifiche non salvate non riapplicate, restano in git stash ({e})")
    return "merged"


if __name__ == "__main__":
    import sys
    if sys.argv[1:2] == ["sync"]:
        try:
            print(f"[sync] {sync_repo()}")
        except Exception as e:  # noqa: BLE001
            print(f"[sync] non riuscito: {e}")
            raise SystemExit(1)
        raise SystemExit(0)
    raise SystemExit(main())
