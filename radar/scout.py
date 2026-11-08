"""Scout balene Hyperliquid: ogni giorno i 3 wallet migliori (conti o vault) da seguire nella pagina Wallet.

Strategia preregistrata in research/scout/PREREG.md (soglie, punteggio, isteresi, verifica): qui la si applica.
1. universo: classifica Hyperliquid (conti ≥ $1M, la stessa di radar/liqmap.py) + vault con TVL ≥ $1M ("copytrading");
   prefiltro economico sulle finestre della classifica (ROI, attività, rotazione da market maker) → ~150 candidati;
2. per ogni candidato la storia `portfolio`: rendimento time-weighted (Modified Dietz, depositi/prelievi neutralizzati),
   max drawdown, R², % periodi positivi, periodo sott'acqua, quota del PnL dai perp; per i migliori anche funding
   (`userFunding`, fino a 365 giorni) e verifica del valore con `clearinghouseState` su tutti i DEX (+ leva attuale);
3. filtri rigidi, allentati in un ordine fisso se passano meno di 3 wallet; punteggio 0–100; isteresi del 15%;
4. verifica: fotografie giornaliere (valore, PnL allTime dalla classifica) delle scelte, di chi ha passato i filtri e di un
   campione di conti ≥ $1M → rendimento a 7/30/90 giorni (data/scout_track.json); ogni 30 giorni, con abbastanza dati,
   piccolo aggiustamento dei pesi verso le componenti che hanno previsto il rendimento successivo.
5. lista osservata (data/wallets_watch.json, esattamente 3 wallet): lo scout NON la cambia. Ogni giorno rianalizza i 3
   osservati e propone fino a 3 candidati che ne battono chiaramente uno (punteggio +15%, oppure l'osservato non passa i
   filtri), con il confronto affiancato; un candidato nuovo arriva su Telegram e l'utente approva con /sostituisci
   (radar/wallets.py.command, letto da radar/journal.py). Le "scelte" Balena 1–3 restano solo per la verifica a 7/30/90 giorni.
Uscite: data/wallet_picks.json e data/wallets_watch.json (lette da cli → report["scout"] e dalla pagina Wallet).
Uso: python -m radar.scout [--force] [--no-telegram]
"""
from __future__ import annotations

import hashlib
import json
import math
import sys
import time
from pathlib import Path

import requests

from . import telegram, wallets
from .liqmap import HL_API, hl_leaderboard

ROOT = Path(__file__).resolve().parents[1]
DATA = ROOT / "data"
PICKS = "wallet_picks.json"
TRACK = "scout_track.json"
WATCH = "wallets_watch.json"   # i 3 wallet osservati e i candidati (radar/wallets.py)
VAULTS = "https://stats-data.hyperliquid.xyz/Mainnet/vaults"
PAGE = "https://andreagalanti91.github.io/radar/#wallet"
DAY = 86400_000
EVERY_H = 20            # un giro al giorno (il workflow è orario): almeno 20 ore fra due giri
VERSION = 1

# ------------------------------------------------------------------ parametri preregistrati (research/scout/PREREG.md)
MIN_VALUE = 1e6
PRE = {"roi_all": 0.5, "roi_month": -0.10, "turnover": 60.0, "top": 150}
HIST_DAYS, MAX_GAP_DAYS = 300, 35
PERP_SHARE = 0.5
CHECK_TOL = 0.10        # valore perp portfolio vs clearinghouseState
TH0 = {"ret": 0.80, "dd": 0.30, "r2": 0.75, "fund": 0.15}
RELAX = [("r2", 0.65), ("dd", 0.35), ("fund", 0.20), ("ret", 0.60)]   # un passo alla volta, in quest'ordine
WEIGHTS0 = {"calmar": 0.40, "r2": 0.25, "pos": 0.20, "fund": 0.15}
N_PICKS, N_RUNNERS, MARGIN = 3, 7, 0.15
N_CAND, DISMISS_DAYS = 3, 30   # al massimo 3 candidati al giorno; un candidato scartato non torna per 30 giorni
N_FUND = 20             # funding e verifica solo per i migliori (costano richieste)
N_BENCH = 120           # campione fisso di conti ≥ $1M per il confronto
HORIZONS = (7, 30, 90)
LEARN_EVERY, LEARN_MIN, LEARN_STEP, LEARN_FLOOR = 30, 30, 0.05, 0.05
ORDER = ["value", "history", "coherence", "active", "perp", "ret", "dd", "r2", "fund", "check"]
LABEL = {"value": "valore < $1M", "history": "storia corta o con buchi", "coherence": "storia incoerente con la classifica",
         "active": "inattivo da 30 giorni", "perp": "PnL non dai perp", "ret": "rendimento 1 anno basso", "dd": "drawdown alto",
         "r2": "crescita irregolare (R²)", "fund": "funding alto (o non verificato)", "check": "verifica valore fallita"}


def thresholds(level: int) -> dict:
    th = dict(TH0)
    for k, v in RELAX[:level]:
        th[k] = v
    return th


# ------------------------------------------------------------------ funzioni pure (tests/test_scout.py)
def points(win: dict) -> list[tuple[int, float, float]]:
    """[(t_ms, valore, pnl_cumulato)] da una finestra di `portfolio` (stessi timestamp nelle due storie)."""
    av = {int(t): float(v) for t, v in win.get("accountValueHistory", [])}
    return sorted((int(t), av[int(t)], float(p)) for t, p in win.get("pnlHistory", []) if int(t) in av)


def md_return(av0: float, pnl0: float, av1: float, pnl1: float) -> float:
    """Modified Dietz di un intervallo: ΔPnL / (valore iniziale + ½ flusso netto); flusso = Δvalore − ΔPnL."""
    dp = pnl1 - pnl0
    flow = (av1 - av0) - dp
    if max(av0, av1) < 1000:
        return 0.0
    den = av0 + 0.5 * flow
    if den <= 0.1 * max(av0, av1):   # depositi/prelievi enormi rispetto al conto: base prudente
        den = max(av0, av1)
    return max(-0.95, min(5.0, dp / den))


def index_of(pts: list) -> list[float]:
    """Indice time-weighted (parte da 1) concatenando i rendimenti Modified Dietz degli intervalli."""
    idx = [1.0]
    for (t0, a0, p0), (t1, a1, p1) in zip(pts, pts[1:]):
        idx.append(idx[-1] * (1 + md_return(a0, p0, a1, p1)))
    return idx


def max_dd(idx: list[float]) -> float:
    peak, dd = -math.inf, 0.0
    for x in idx:
        peak = max(peak, x)
        if peak > 0:
            dd = max(dd, 1 - x / peak)
    return dd


def r2_log(ts: list[float], idx: list[float]) -> float:
    """R² della retta log(indice) ~ tempo: 1 = crescita composta perfettamente regolare."""
    if len(idx) < 3 or min(idx) <= 0:
        return 0.0
    y = [math.log(x) for x in idx]
    n = len(y)
    mx, my = sum(ts) / n, sum(y) / n
    sxx = sum((x - mx) ** 2 for x in ts)
    syy = sum((v - my) ** 2 for v in y)
    if sxx == 0 or syy == 0:
        return 0.0
    sxy = sum((x - mx) * (v - my) for x, v in zip(ts, y))
    b = sxy / sxx
    if b <= 0:
        return 0.0   # una retta in discesa non è "crescita regolare"
    return sxy * sxy / (sxx * syy)


def underwater_days(ts: list[float], idx: list[float]) -> float:
    """Periodo più lungo (giorni) passato sotto il massimo precedente, anche se non ancora recuperato."""
    best, peak, t_peak = 0.0, -math.inf, None
    for t, x in zip(ts, idx):
        if x >= peak:
            if t_peak is not None:
                best = max(best, t - t_peak)
            peak, t_peak = x, t
    if t_peak is not None and idx and idx[-1] < peak:
        best = max(best, ts[-1] - t_peak)
    return best


def _anchor(pts: list, start: int) -> int:
    """Indice dell'ultimo punto ≤ start (0 se la storia comincia dopo)."""
    i0 = 0
    for i, p in enumerate(pts):
        if p[0] <= start:
            i0 = i
    return i0


def metrics(port, now_ms: int) -> dict:
    """Metriche sull'ultimo anno dalla risposta di `portfolio` (lista [[finestra, {...}], ...] o dict)."""
    P = dict(port)
    pts = points(P.get("allTime", {}))
    if len(pts) < 3:
        return {"ok": False, "why": "storia vuota", "history_days": 0}
    start = now_ms - 365 * DAY
    i0 = _anchor(pts, start)
    seg = pts[i0:]
    hist = (now_ms - pts[0][0]) / DAY
    gaps = [(b[0] - a[0]) / DAY for a, b in zip(seg, seg[1:])]
    span = (seg[-1][0] - seg[0][0]) / DAY
    ts = [(p[0] - seg[0][0]) / DAY for p in seg]
    idx = index_of(seg)
    raw = idx[-1] - 1
    ret = (1 + raw) ** (365 / span) - 1 if span > 0 and raw > -1 else raw
    dds = [max_dd(idx)]
    for w in ("month", "week"):
        p2 = points(P.get(w, {}))
        if len(p2) >= 3:
            dds.append(max_dd(index_of(p2)))
    rs = [b / a - 1 for a, b in zip(idx, idx[1:]) if a > 0]
    pnl_y = seg[-1][2] - seg[0][2]
    pp = points(P.get("perpAllTime", {}))
    perp_y = None
    if len(pp) >= 2:
        j0 = _anchor(pp, seg[0][0])
        perp_y = pp[-1][2] - pp[j0][2]
    mo = points(P.get("month", {}))   # ultimi 30 giorni a punti fitti: rendimento e volume recenti (confronto dei candidati)
    ret30 = (index_of(mo)[-1] - 1) if len(mo) >= 2 else None
    vlm30 = float((P.get("month") or {}).get("vlm") or 0)
    return {
        "ret_30d": ret30, "vlm_30d": vlm30,
        "ok": True, "history_days": round(hist, 1), "span_days": round(span, 1), "max_gap_days": round(max(gaps) if gaps else 0, 1),
        "negative": any(p[1] < -1 for p in seg), "ret_1y": ret, "dd": max(dds), "dd_1y": dds[0], "r2": r2_log(ts, idx),
        "pos": (sum(r > 0 for r in rs) / len(rs)) if rs else 0.0, "underwater_days": round(underwater_days(ts, idx), 1),
        "pnl_1y": pnl_y, "perp_pnl_1y": perp_y, "perp_share": (perp_y / pnl_y) if (perp_y is not None and pnl_y > 0) else None,
        "value": seg[-1][1], "pnl_all": pts[-1][2], "avg_cap": sum(p[1] for p in seg) / len(seg),
        "perp_value": pp[-1][1] if pp else None, "n_points": len(seg),
        "curve": [[int(p[0] // 1000), round(x, 4)] for p, x in zip(seg, idx)],
    }


def pnl_between(port, t0: int, t1: int) -> float | None:
    """PnL fra i punti allTime più vicini (≤) a t0 e a t1: base del funding % sullo stesso periodo."""
    pts = points(dict(port).get("allTime", {}))
    if len(pts) < 2 or t1 <= t0:
        return None
    return pts[_anchor(pts, t1)][2] - pts[_anchor(pts, t0)][2]


def funding_stats(entries: list[dict], pnl_window: float | None, avg_cap: float) -> dict:
    """Funding netto (positivo = incassato) e costo pagato in % del PnL e del capitale dello stesso periodo."""
    net = sum(float((e.get("delta") or {}).get("usdc") or 0) for e in entries)
    cost = max(0.0, -net)
    of_pnl = (cost / pnl_window) if pnl_window and pnl_window > 0 else (0.0 if cost == 0 else math.inf)
    return {"funding_net": net, "funding_cost": cost, "fund_pnl": of_pnl, "fund_cap": cost / avg_cap if avg_cap > 0 else None}


def fails(m: dict, th: dict) -> list[str]:
    """Filtri rigidi non superati, nell'ordine di ORDER. Un dato mancante (funding, verifica) conta come non superato."""
    out = []
    if (m.get("value") or 0) < MIN_VALUE:
        out.append("value")
    if not m.get("ok") or m.get("history_days", 0) < HIST_DAYS or m.get("max_gap_days", 99) > MAX_GAP_DAYS or m.get("negative"):
        out.append("history")
    if m.get("coherent") is False:
        out.append("coherence")
    if not m.get("active", True):
        out.append("active")
    ps = m.get("perp_share")
    if m.get("pnl_1y", 0) > 0 and (ps is None or ps < PERP_SHARE):   # con PnL ≤ 0 conta il filtro del rendimento
        out.append("perp")
    if not (m.get("ret_1y", -1) > th["ret"]):
        out.append("ret")
    if m.get("dd", 1) > th["dd"]:
        out.append("dd")
    if m.get("r2", 0) < th["r2"]:
        out.append("r2")
    if m.get("fund_pnl") is None or m["fund_pnl"] > th["fund"]:
        out.append("fund")
    if m.get("check_ok") is False:
        out.append("check")
    return [k for k in ORDER if k in out]


def components(m: dict) -> dict:
    cal = m.get("ret_1y", 0) / max(m.get("dd", 1), 0.05)
    fp = m.get("fund_pnl")
    return {
        "calmar": min(1.0, max(0.0, math.log1p(max(cal, 0)) / math.log(21))),
        "r2": min(1.0, max(0.0, (m.get("r2", 0) - 0.5) / 0.5)),
        "pos": min(1.0, max(0.0, m.get("pos", 0))),
        "fund": 1.0 if fp is None else 1 - min(1.0, max(0.0, fp) / TH0["fund"]),
    }


def score(m: dict, w: dict | None = None) -> float:
    w = w or WEIGHTS0
    c = components(m)
    return round(100 * sum(w[k] * c[k] for k in w) / sum(w.values()), 2)


def select(ranked: list[tuple[str, float]], current: list[str], n: int = N_PICKS, margin: float = MARGIN) -> list[str]:
    """Isteresi: chi è già scelto e passa resta, salvo uno sfidante con punteggio > (1 + margin) × il più debole."""
    sc = dict(ranked)
    picks = [a for a in current if a in sc][:n]
    others = [a for a, _ in sorted(ranked, key=lambda x: -x[1]) if a not in picks]
    while len(picks) < n and others:
        picks.append(others.pop(0))
    for c in others:
        weak = min(picks, key=lambda a: sc[a])
        if sc[c] > sc[weak] * (1 + margin):
            picks[picks.index(weak)] = c
        else:
            break
    return sorted(picks, key=lambda a: -sc[a])


def slots(new: list[str], old: dict[str, int], n: int = N_PICKS) -> dict[str, int]:
    """Posto fisso (Balena 1–3): chi resta tiene il suo numero, chi entra prende il primo libero."""
    keep = {a: s for a, s in old.items() if a in new}
    free = [s for s in range(1, n + 1) if s not in keep.values()]
    for a in new:
        if a not in keep:
            keep[a] = free.pop(0)
    return keep


def beats(c: dict, w: dict, margin: float = MARGIN) -> str | None:
    """Motivo per cui il candidato c (passa i filtri) batte chiaramente il wallet osservato w, oppure None.
    Isteresi come per le scelte: punteggio oltre (1 + margin) × quello dell'osservato, oppure l'osservato non passa i filtri
    (e il candidato ha comunque un punteggio più alto)."""
    if c.get("fails") or c.get("score") is None or w.get("score") is None:
        return None
    if w.get("fails"):
        if c["score"] > w["score"]:
            fl = [LABEL.get(f, f) for f in w["fails"]]
            more = f" e altri {len(fl) - 2}" if len(fl) > 2 else ""
            return (f"{w.get('name', 'l’osservato')} non passa i filtri ({', '.join(fl[:2])}{more}); "
                    f"punteggio {c['score']:.0f} contro {w['score']:.0f}")
        return None
    if c["score"] > w["score"] * (1 + margin):
        return f"punteggio {c['score']:.0f} contro {w['score']:.0f} (+{(c['score'] / w['score'] - 1) * 100:.0f}%, soglia +{margin * 100:.0f}%)"
    return None


def pick_candidates(watch: list[dict], ranked: list[dict], dismissed: set[str] = frozenset(), n: int = N_CAND,
                    margin: float = MARGIN) -> list[dict]:
    """Fino a n candidati fra chi passa i filtri (ranked: dict con address, score, fails; dal punteggio più alto). Ognuno va
    contro il posto più debole che batte (prima chi non passa i filtri, poi il punteggio più basso), preferendo un posto
    non ancora preso da un altro candidato. watch: [{slot, address, name, score, fails}]."""
    have = {w["address"] for w in watch}
    out, used = [], set()
    for c in sorted(ranked, key=lambda c: -(c.get("score") or 0)):
        if c["address"] in have or c["address"] in dismissed:
            continue
        ok = [(w, r) for w in watch if (r := beats(c, w, margin))]
        if not ok:
            continue
        ok.sort(key=lambda x: (not x[0].get("fails"), x[0].get("score") or 0))
        w, r = next((x for x in ok if x[0]["slot"] not in used), ok[0])
        used.add(w["slot"])
        out.append({"address": c["address"], "slot": w["slot"], "reason": r})
        if len(out) >= n:
            break
    return out


def cand_id(a: str, taken: set[str]) -> str:
    """Id breve del candidato per i comandi Telegram: 4 cifre esadecimali dell'indirizzo (6 se già prese)."""
    k = a[2:6]
    return k if k not in taken else a[2:8]


def _fills(api, a: str, now_ms: int) -> float | None:
    try:
        return round(fills_per_day(api.post({"type": "userFills", "user": a, "aggregateByTime": True}, 20) or [], now_ms), 2)
    except Exception:  # noqa: BLE001
        return None


def update_watch(watch: dict, by: dict, passing: list[dict], today: str, entry, fills=None) -> list[dict]:
    """Aggiorna le metriche dei 3 osservati e i candidati (sul posto). Ritorna i candidati da notificare (mai notificati)."""
    wl = []
    for x in watch["slots"]:
        m = by.get(x["address"])
        if not m or not m.get("ok"):
            continue
        x.update(score=m["score"], fails=[LABEL[f] for f in m["fails"]], metrics=_slim(m), checked=today, curve=m.get("curve", [])[-30:],
                 why=why(m))
        wl.append({"slot": x["slot"], "address": x["address"], "name": x["name"], "score": m["score"], "fails": m["fails"]})
    watch["dismissed"] = {a: d for a, d in (watch.get("dismissed") or {}).items() if _days(d, today) < DISMISS_DAYS}
    found = pick_candidates(wl, [m for m in passing if m.get("ok")], set(watch["dismissed"]))
    prevc = {c["address"]: c for c in watch.get("candidates", [])}
    out, taken = [], set()
    for f in found:
        a, m = f["address"], by[f["address"]]
        vs = watch["slots"][f["slot"] - 1]
        if m.get("fills_day") is None and fills:
            m["fills_day"] = fills(a)
        e = entry(m)
        cid = prevc.get(a, {}).get("id") or cand_id(a, taken)
        taken.add(cid)
        out.append({"id": cid, "address": a, "name": e["name"] if e["kind"] == "vault" else f"Balena {cid}", "display": m.get("display"),
                    "kind": e["kind"], "leader_of": e.get("leader_of"), "slot": f["slot"], "vs_name": vs["name"], "vs_address": vs["address"],
                    "reason": f["reason"], "score": m["score"], "vs_score": vs.get("score"), "metrics": _slim(m), "vs_metrics": vs.get("metrics") or {},
                    "fails": [], "vs_fails": vs.get("fails", []), "why": e["why"], "curve": e["curve"], "vs_curve": vs.get("curve", []),
                    "date": today, "first": prevc.get(a, {}).get("first") or today, "notified": prevc.get(a, {}).get("notified")})
    watch["candidates"] = out
    watch["updated"] = today
    return [c for c in out if not c.get("notified")]


def chain_return(seq: list[tuple[float, float]]) -> tuple[float, float]:
    """Rendimento e max drawdown concatenando le fotografie [(valore, pnl)] (Modified Dietz fra due fotografie)."""
    idx = [1.0]
    for (a0, p0), (a1, p1) in zip(seq, seq[1:]):
        idx.append(idx[-1] * (1 + md_return(a0, p0, a1, p1)))
    return idx[-1] - 1, max_dd(idx)


def median(xs: list[float]) -> float | None:
    xs = sorted(x for x in xs if x is not None and math.isfinite(x))
    if not xs:
        return None
    k = len(xs) // 2
    return xs[k] if len(xs) % 2 else (xs[k - 1] + xs[k]) / 2


def spearman(x: list[float], y: list[float]) -> float:
    def rank(v):
        o = sorted(range(len(v)), key=lambda i: v[i])
        r = [0.0] * len(v)
        i = 0
        while i < len(o):
            j = i
            while j + 1 < len(o) and v[o[j + 1]] == v[o[i]]:
                j += 1
            for k in range(i, j + 1):
                r[o[k]] = (i + j) / 2
            i = j + 1
        return r
    if len(x) < 3:
        return 0.0
    rx, ry = rank(x), rank(y)
    n = len(x)
    mx, my = sum(rx) / n, sum(ry) / n
    sxy = sum((a - mx) * (b - my) for a, b in zip(rx, ry))
    sxx = sum((a - mx) ** 2 for a in rx)
    syy = sum((b - my) ** 2 for b in ry)
    return sxy / math.sqrt(sxx * syy) if sxx and syy else 0.0


def learn(weights: dict, obs: list[list[float]]) -> tuple[dict, dict]:
    """Un passo: ogni peso si sposta di 0,1 × Spearman(componente, rendimento a 30g), al massimo ±LEARN_STEP, poi somma 1."""
    keys = list(WEIGHTS0)
    if len(obs) < LEARN_MIN:
        return dict(weights), {"applied": False, "n": len(obs)}
    y = [o[-1] for o in obs]
    rho = {k: spearman([o[i] for o in obs], y) for i, k in enumerate(keys)}
    w = {k: max(LEARN_FLOOR, weights[k] + max(-LEARN_STEP, min(LEARN_STEP, 0.1 * rho[k]))) for k in keys}
    s = sum(w.values())
    return {k: round(v / s, 4) for k, v in w.items()}, {"applied": True, "n": len(obs), "rho": {k: round(v, 3) for k, v in rho.items()}}


def prefilter(rows: list[dict], vault_set: set[str], skip: set[str]) -> tuple[list[dict], dict]:
    """Conti ≥ $1M della classifica → candidati (prefiltro economico). I vault passano tutti (sono pochi)."""
    rej = {"pnl_roi": 0, "month": 0, "inactive": 0, "turnover": 0, "system": 0}
    out = []
    for r in rows:
        a = r["ethAddress"].lower()
        av = float(r.get("accountValue") or 0)
        if av < MIN_VALUE:
            continue
        if a in skip:
            rej["system"] += 1
            continue
        w = {k: {kk: float(vv or 0) for kk, vv in d.items()} for k, d in r.get("windowPerformances", [])}
        al, mo = w.get("allTime", {}), w.get("month", {})
        c = {"address": a, "value_lb": av, "display": r.get("displayName"), "roi_all": al.get("roi", 0), "roi_month": mo.get("roi", 0),
             "pnl_lb": al.get("pnl", 0), "vlm_month": mo.get("vlm", 0), "vault": a in vault_set}
        if c["vault"]:
            out.append(c)
            continue
        if not (al.get("pnl", 0) > 0 and al.get("roi", 0) > PRE["roi_all"]):
            rej["pnl_roi"] += 1
        elif mo.get("roi", 0) <= PRE["roi_month"]:
            rej["month"] += 1
        elif mo.get("vlm", 0) <= 0:
            rej["inactive"] += 1
        elif mo.get("vlm", 0) / av > PRE["turnover"]:
            rej["turnover"] += 1
        else:
            out.append(c)
    accts = sorted([c for c in out if not c["vault"]], key=lambda c: -(min(c["roi_all"], 3) + c["roi_month"]))
    rej["beyond_top"] = max(0, len(accts) - PRE["top"])
    return [c for c in out if c["vault"]] + accts[:PRE["top"]], rej


def bench_sample(addrs: list[str], n: int = N_BENCH) -> list[str]:
    """Campione fisso (per hash dell'indirizzo, non per risultato) dei conti ≥ $1M."""
    return sorted(addrs, key=lambda a: hashlib.sha1(a.encode()).hexdigest())[:n]


def pct(x, d=0):
    return "–" if x is None or not math.isfinite(x) else f"{x * 100:.{d}f}%".replace(".", ",")


def why(m: dict) -> str:
    return (f"{'+' if m['ret_1y'] >= 0 else ''}{pct(m['ret_1y'])} in un anno (time-weighted), drawdown max {pct(m['dd'])}, "
            f"R² {m['r2']:.2f}".replace(".", ",") + f", {pct(m['pos'])} dei periodi di 2 settimane positivi, "
            f"funding {pct(m.get('fund_pnl'), 1)} del PnL" + (f", leva attuale {m['lev']:.1f}x".replace(".", ",") if m.get("lev") is not None else ""))


# ------------------------------------------------------------------ rete (Hyperliquid, con budget di peso)
class Api:
    """POST info con budget di peso al minuto (limite Hyperliquid ~1200/min per IP: qui 900) e attesa sui 429."""

    def __init__(self, budget: int = 900):
        self.s, self.budget, self.log, self.calls = requests.Session(), budget, [], 0

    def post(self, body: dict, weight: int = 20):
        now = time.time()
        self.log = [(t, w) for t, w in self.log if now - t < 60]
        while sum(w for _, w in self.log) + weight > self.budget:
            time.sleep(1.0)
            now = time.time()
            self.log = [(t, w) for t, w in self.log if now - t < 60]
        for k in range(5):
            self.log.append((time.time(), weight))
            self.calls += 1
            try:
                r = self.s.post(HL_API, json=body, timeout=30)
            except requests.RequestException:
                time.sleep(2 + 3 * k)
                continue
            if r.status_code == 429:
                time.sleep(5 * (k + 1))
                continue
            r.raise_for_status()
            return r.json()
        raise RuntimeError("Hyperliquid: troppe richieste")


def fetch_funding(api: Api, a: str, now_ms: int, max_pages: int = 10) -> tuple[list[dict], int, int]:
    """userFunding: prima gli ultimi 90 giorni, poi (se le pagine bastano) 90–365 giorni; pagine da 500 voci.
    Le voci recenti sono orarie per coin: un conto con decine di coin riempie le pagine in fretta. Se i 90 giorni non
    finiscono si usa il tratto letto (dall'inizio dei 90 giorni a dove si è arrivati). Ritorna (voci, da, a) in ms."""
    out, pages, t_from, t_to = [], 0, now_ms, now_ms
    for lo, hi in ((90, 0), (365, 90)):
        start, end = now_ms - lo * DAY, now_ms - hi * DAY
        chunk, seen, complete, reached = [], set(), True, start
        while True:
            if pages >= max_pages:
                complete = False
                break
            rows = api.post({"type": "userFunding", "user": a, "startTime": start, "endTime": end}, 20) or []
            pages += 1
            api.log.append((time.time(), len(rows) // 20))   # peso extra: 1 ogni 20 voci
            for e in rows:
                k = (e.get("time"), (e.get("delta") or {}).get("coin"), (e.get("delta") or {}).get("usdc"))
                if k not in seen:
                    seen.add(k)
                    chunk.append(e)
            if len(rows) < 500:
                break
            nxt = max(int(e["time"]) for e in rows)   # stessa ora per più coin: si riparte da lì e si tolgono i doppioni
            if nxt <= start:
                break
            start = reached = nxt
        if complete:
            out += chunk
            t_from = now_ms - lo * DAY
            continue
        if lo == 90:   # 90 giorni non finiti: si tiene il tratto [inizio, ultima ora letta), senza l'ultima ora (forse parziale)
            out = [e for e in chunk if int(e["time"]) < reached]
            t_from, t_to = now_ms - lo * DAY, reached
        break
    return out, t_from, t_to


def cross_check(api: Api, a: str, dexes: list[str], perp_value: float | None) -> dict:
    """Valore perp da clearinghouseState (tutti i DEX) contro portfolio, e leva attuale (esposizione / valore)."""
    av, ntl = 0.0, 0.0
    for d in dexes:
        cs = api.post({"type": "clearinghouseState", "user": a, **({"dex": d} if d else {})}, 2)
        if not cs:
            continue
        av += float(cs["marginSummary"]["accountValue"])
        ntl += sum(abs(float(p["position"]["positionValue"])) for p in cs.get("assetPositions", []))
    ok = None
    if perp_value is not None and max(av, perp_value) > 1000:
        ok = abs(av - perp_value) <= CHECK_TOL * max(av, perp_value, 1.0) + 1000
    return {"ch_value": av, "check_ok": ok, "lev": ntl / av if av > 0 else 0.0, "exposure": ntl}


def fills_per_day(fills: list[dict], now_ms: int) -> float:
    """Operazioni (fill aggregati) al giorno negli ultimi 30 giorni; userFills dà al massimo 2.000 fill: se il tetto è pieno
    si divide per il tratto davvero coperto."""
    ts = [int(f.get("time") or 0) for f in fills or []]
    rec = [t for t in ts if t >= now_ms - 30 * DAY]
    if not rec:
        return 0.0
    span = 30.0 if len(ts) < 2000 else max((now_ms - min(ts)) / DAY, 1 / 24)
    return len(rec) / min(30.0, span)


def profile(api: Api, a: str, now_ms: int, dexes: list[str], lb: dict | None = None) -> dict:
    """Tutte le metriche dello scout per un solo indirizzo (wallet osservati e confronto dei candidati): storia `portfolio`,
    funding, verifica del valore e leva attuale, attività. lb = riga compatta della classifica, se c'è (coerenza e attività)."""
    port = api.post({"type": "portfolio", "user": a}, 20)
    m = metrics(port, now_ms)
    m["address"] = a
    if not m.get("ok"):
        m.setdefault("value", (lb or {}).get("value_lb"))
        return m
    lbp = (lb or {}).get("pnl_lb")
    m["coherent"] = None if lbp is None else abs(m["pnl_all"] - lbp) <= max(0.10 * abs(lbp), 50_000)
    m["active"] = (m.get("vlm_30d") or 0) > 0
    ent, t0, t1 = fetch_funding(api, a, now_ms)
    if t1 - t0 >= 30 * DAY:
        m.update(funding_stats(ent, pnl_between(port, t0, t1), m["avg_cap"] * (t1 - t0) / (365 * DAY)))
        m["fund_days"] = round((t1 - t0) / DAY)
    m.update(cross_check(api, a, dexes, m.get("perp_value")))
    try:
        m["fills_day"] = round(fills_per_day(api.post({"type": "userFills", "user": a, "aggregateByTime": True}, 20) or [], now_ms), 2)
    except Exception:  # noqa: BLE001
        m["fills_day"] = None
    return m


def _load(p: Path, default):
    try:
        return json.loads(p.read_text()) if p.exists() else default
    except Exception:  # noqa: BLE001
        return default


def _iso(ms: int) -> str:
    return time.strftime("%Y-%m-%d", time.gmtime(ms / 1000))


def _days(a: str, b: str) -> int:
    return round((time.mktime(time.strptime(b, "%Y-%m-%d")) - time.mktime(time.strptime(a, "%Y-%m-%d"))) / 86400)


# ------------------------------------------------------------------ verifica e apprendimento
def update_track(track: dict, today: str, lbmap: dict, picks: list[dict], passed: list[dict], bench: list[str]) -> dict:
    """Aggiunge la coorte di oggi, valuta le coorti passate a 7/30/90 giorni, fa (se è il momento) un passo di apprendimento."""
    track.setdefault("weights", dict(WEIGHTS0))
    track.setdefault("learn", {"last": None, "steps": []})
    track.setdefault("cohorts", [])
    track.setdefault("snaps", {})
    track.setdefault("done", [])
    v = lambda a: lbmap.get(a)   # noqa: E731
    # fotografie giornaliere delle scelte (servono per il drawdown dopo la scelta)
    tracked = {p["address"] for p in picks} | {x[0] for c in track["cohorts"] for x in c["picks"]}
    track["snaps"][today] = {a: v(a) for a in sorted(tracked) if v(a)}
    if not any(c["date"] == today for c in track["cohorts"]):
        track["cohorts"].append({
            "date": today,
            "picks": [[p["address"], *v(p["address"])] for p in picks if v(p["address"])],
            "passed": [[c["address"], *v(c["address"]), *[round(x, 4) for x in components(c).values()]] for c in passed if v(c["address"])],
            "bench": [[a, *v(a)] for a in bench if v(a)], "ev": {},
        })
    snap_days = sorted(track["snaps"])
    for c in track["cohorts"]:
        age = _days(c["date"], today)
        for h in HORIZONS:
            if str(h) in c["ev"] or age < h:
                continue
            def ret(x):
                cur = v(x[0])
                return md_return(x[1], x[2], cur[0], cur[1]) if cur else None
            pr = [ret(x) for x in c["picks"]]
            dds = []
            for x in c["picks"]:
                seq = [(x[1], x[2])] + [tuple(track["snaps"][d][x[0]]) for d in snap_days if c["date"] < d <= today and x[0] in track["snaps"][d]]
                dds.append(chain_return(seq)[1])
            ps = [ret(x) for x in c["passed"]]
            bs = [ret(x) for x in c["bench"]]
            ok = [r for r in pr if r is not None]
            e = {"days": age, "picks": [None if r is None else round(r, 4) for r in pr],
                 "pick_mean": round(sum(ok) / len(ok), 4) if ok else None, "pick_dd": round(max(dds), 4) if dds else None,
                 "passed_med": median(ps), "bench_med": median(bs), "n_passed": sum(r is not None for r in ps), "n_bench": sum(r is not None for r in bs)}
            if h == 30:
                e["obs"] = [[*x[3:7], round(r, 4)] for x, r in zip(c["passed"], ps) if r is not None]
            c["ev"][str(h)] = e
    # coorti completate (90 giorni valutati): resta solo il riassunto
    keep = []
    for c in track["cohorts"]:
        if "90" in c["ev"]:
            track["done"].append({"date": c["date"], "picks": [x[0] for x in c["picks"]],
                                  "ev": {h: {k: x for k, x in e.items() if k != "obs"} for h, e in c["ev"].items()}})
        else:
            keep.append(c)
    track["cohorts"] = keep
    track["done"] = track["done"][-400:]
    live = {x[0] for c in keep for x in c["picks"]} | {p["address"] for p in picks}
    first = keep[0]["date"] if keep else today
    track["snaps"] = {d: {a: x for a, x in s.items() if a in live} for d, s in track["snaps"].items() if d >= first}
    # apprendimento: ogni 30 giorni, solo con abbastanza osservazioni a 30 giorni
    L = track["learn"]
    started = min([c["date"] for c in keep] + [d["date"] for d in track["done"]] + [today])
    if _days(L["last"] or started, today) >= LEARN_EVERY:
        obs = [o for c in keep for o in c["ev"].get("30", {}).get("obs", [])]
        w, info = learn(track["weights"], obs)
        L["last"] = today
        L["steps"].append({"date": today, **info, "weights": w})
        L["steps"] = L["steps"][-24:]
        track["weights"] = w
    return track


def track_summary(track: dict) -> dict:
    out = {}
    allc = track.get("cohorts", []) + track.get("done", [])
    for h in HORIZONS:
        ev = [c["ev"][str(h)] for c in allc if str(h) in c.get("ev", {}) and c["ev"][str(h)].get("pick_mean") is not None]
        if not ev:
            out[str(h)] = {"n": 0}
            continue
        mean = lambda k: (lambda xs: sum(xs) / len(xs) if xs else None)([e[k] for e in ev if e.get(k) is not None])   # noqa: E731
        out[str(h)] = {"n": len(ev), "pick": mean("pick_mean"), "passed": mean("passed_med"), "bench": mean("bench_med"),
                       "dd": mean("pick_dd"), "beat_passed": sum(1 for e in ev if e.get("passed_med") is not None and e["pick_mean"] > e["passed_med"]) / len(ev),
                       "beat_bench": sum(1 for e in ev if e.get("bench_med") is not None and e["pick_mean"] > e["bench_med"]) / len(ev)}
    return out


# ------------------------------------------------------------------ giro completo
def _slim(c: dict) -> dict:
    keys = ("ret_1y", "dd", "dd_1y", "r2", "pos", "underwater_days", "fund_pnl", "fund_cap", "funding_net", "fund_days", "value", "pnl_1y",
            "perp_share", "lev", "history_days", "check_ok", "ch_value", "perp_value", "ret_30d", "vlm_30d", "fills_day")
    m = {k: (None if isinstance(c.get(k), float) and not math.isfinite(c[k]) else (round(c[k], 4) if isinstance(c.get(k), float) else c.get(k))) for k in keys}
    return m


def run(data_dir: Path = DATA, send: bool = True, now_ms: int | None = None, log=print) -> dict:
    t_start = time.time()
    now_ms = now_ms or int(time.time() * 1000)
    today = _iso(now_ms)
    prev = _load(data_dir / PICKS, {})
    track = _load(data_dir / TRACK, {})
    W = track.get("weights") or dict(WEIGHTS0)
    api = Api()
    rows = hl_leaderboard()
    lbmap = {r["ethAddress"].lower(): [round(float(r.get("accountValue") or 0)), round(float(dict(r.get("windowPerformances", [])).get("allTime", {}).get("pnl") or 0))]
             for r in rows}
    vaults = requests.get(VAULTS, timeout=90).json()
    vinfo, skip = {}, set()
    for x in vaults:
        s = x.get("summary", {})
        a = s.get("vaultAddress", "").lower()
        rel = (s.get("relationship") or {}).get("type")
        tvl = float(s.get("tvl") or 0)
        if rel in ("parent", "child"):        # HLP e i suoi vault figli: liquidità del protocollo, non un trader
            skip.add(a)
            continue
        if s.get("isClosed") or tvl < MIN_VALUE:
            continue
        vinfo[a] = {"name": s.get("name"), "leader": (s.get("leader") or "").lower(), "tvl": tvl, "apr": x.get("apr")}
    leaders = {v["leader"]: v["name"] for v in vinfo.values()}
    big = [r for r in rows if float(r.get("accountValue") or 0) >= MIN_VALUE]
    cands, pre_rej = prefilter(big, set(vinfo), skip)
    have = {c["address"] for c in cands}
    for a, v in vinfo.items():            # vault ≥ $1M assenti dalla classifica
        if a not in have:
            cands.insert(0, {"address": a, "value_lb": v["tvl"], "display": None, "roi_all": None, "roi_month": None, "pnl_lb": None, "vlm_month": None, "vault": True})
            have.add(a)
    watch = wallets.load_watch(data_dir / WATCH)
    wset = {x["address"].lower() for x in watch["slots"]} | {o["address"] for o in ((watch.get("review") or {}).get("options") or [])}
    rowmap = {r["ethAddress"].lower(): r for r in rows}
    # le scelte attuali (isteresi) e i 3 wallet osservati (confronto con i candidati) si rianalizzano sempre
    for a in [p["address"] for p in prev.get("picks", [])] + sorted(wset):
        if a in have:
            continue
        r = rowmap.get(a)
        if r is None and a not in wset:
            continue
        w = {k: {kk: float(vv or 0) for kk, vv in d.items()} for k, d in (r or {}).get("windowPerformances", [])}
        cands.append({"address": a, "value_lb": lbmap[a][0] if r else None, "display": (r or {}).get("displayName"), "roi_all": w.get("allTime", {}).get("roi"),
                      "roi_month": w.get("month", {}).get("roi"), "pnl_lb": w.get("allTime", {}).get("pnl"), "vlm_month": w.get("month", {}).get("vlm"), "vault": a in vinfo})
        have.add(a)
    log(f"[scout] classifica {len(rows)} conti, {len(big)} ≥ $1M · vault ≥ $1M {len(vinfo)} · candidati {len(cands)}")
    analyzed, ports = [], {}
    for i, c in enumerate(cands):
        try:
            port = api.post({"type": "portfolio", "user": c["address"]}, 20)
        except Exception as e:  # noqa: BLE001
            log(f"[scout] portfolio {c['address']}: {e!r}")
            continue
        m = metrics(port, now_ms)
        m.update(c)
        if m.get("ok"):
            ports[c["address"]] = port
            lbp = c.get("pnl_lb")
            m["coherent"] = None if lbp is None else abs(m["pnl_all"] - lbp) <= max(0.10 * abs(lbp), 50_000)
            if m["coherent"] is False:
                log(f"[scout] storia incoerente {c['address']}: PnL portfolio {m['pnl_all']:,.0f} vs classifica {lbp:,.0f}")
        m["active"] = (m.get("vlm_30d") or 0) > 0 if c.get("vlm_month") is None else c["vlm_month"] > 0
        if m.get("value") is None:
            m["value"] = c["value_lb"] or 0
        analyzed.append(m)
        if (i + 1) % 25 == 0:
            log(f"[scout] {i + 1}/{len(cands)} analizzati ({time.time() - t_start:.0f} s)")
    # funding e verifica: solo i migliori che passano tutto il resto al livello più largo
    loosest = thresholds(len(RELAX))
    core = [m for m in analyzed if not [f for f in fails(m, loosest) if f not in ("fund", "check")]]
    core.sort(key=lambda m: -score(m, W))
    dexes = [""] + [d["name"] for d in (api.post({"type": "perpDexs"}, 20) or []) if d]
    top = core[:N_FUND]
    extra = [m for m in analyzed if m["address"] in wset and m.get("ok") and m not in top]   # osservati: sempre verificati
    for m in top + extra:
        a = m["address"]
        try:
            if a in wset:
                m["fills_day"] = round(fills_per_day(api.post({"type": "userFills", "user": a, "aggregateByTime": True}, 20) or [], now_ms), 2)
            ent, t0, t1 = fetch_funding(api, a, now_ms)
            if t1 - t0 >= 30 * DAY:   # meno di 30 giorni letti: funding non verificato
                m.update(funding_stats(ent, pnl_between(ports[a], t0, t1), m["avg_cap"] * (t1 - t0) / (365 * DAY)))
                m["fund_days"] = round((t1 - t0) / DAY)
            m.update(cross_check(api, a, dexes, m.get("perp_value")))
        except Exception as e:  # noqa: BLE001
            log(f"[scout] funding/verifica {a}: {e!r}")
    for m in core[N_FUND:]:
        if m["address"] not in wset:
            m["fund_skipped"] = True
    # livello di allentamento: il primo con almeno 3 wallet che passano
    level, passing = 0, []
    for level in range(len(RELAX) + 1):
        th = thresholds(level)
        passing = [m for m in analyzed if not fails(m, th)]
        if len(passing) >= N_PICKS:
            break
    th = thresholds(level)
    for m in analyzed:
        m["score"] = score(m, W)
        m["fails"] = fails(m, th)
    passing.sort(key=lambda m: -m["score"])
    cur = [p["address"] for p in prev.get("picks", [])]
    chosen = select([(m["address"], m["score"]) for m in passing], cur)
    old_slots = {p["address"]: p.get("slot") for p in prev.get("picks", []) if p.get("slot")}
    sl = slots(chosen, old_slots)
    by = {m["address"]: m for m in analyzed}
    since = {p["address"]: p.get("since") for p in prev.get("picks", [])}

    def entry(m, slot=None):
        a = m["address"]
        vault = vinfo.get(a)
        name = vault["name"] if vault else f"Balena {slot}" if slot else (m.get("display") or a[:6] + "…" + a[-4:])
        return {"slot": slot, "address": a, "name": name, "kind": "vault" if vault else "conto", "display": m.get("display"),
                "leader_of": leaders.get(a), "score": m["score"], "metrics": _slim(m), "why": why(m) if m.get("ok") else "",
                "fails": [LABEL[f] for f in m["fails"]], "curve": m.get("curve", [])[-30:]}
    picks = []
    for a in chosen:
        e = entry(by[a], sl[a])
        e["since"] = since.get(a) or today
        e["kept"] = a in cur
        picks.append(e)
    picks.sort(key=lambda p: p["slot"])
    rest = [m for m in passing if m["address"] not in chosen]
    structural = {"value", "history", "coherence", "active", "perp"}   # riserve: solo chi manca un filtro di qualità
    near = sorted([m for m in analyzed if m["fails"] and m.get("ok") and not structural & set(m["fails"]) and m["address"] not in chosen],
                  key=lambda m: (len(m["fails"]), -m["score"]))
    runners = [entry(m) for m in (rest + near)[:N_RUNNERS]]
    rejected = {LABEL[k]: 0 for k in ORDER}
    for m in analyzed:
        f = fails(m, TH0)
        if f:
            rejected[LABEL[f[0]]] += 1
    changed = sorted(chosen) != sorted(cur)
    hist = prev.get("history", [])
    if changed or not hist:
        hist.append({"date": today, "picks": [[p["address"], p["name"]] for p in picks], "level": level,
                     "in": [p["name"] for p in picks if not p["kept"]], "out": [x[1] for x in (hist[-1]["picks"] if hist else []) if x[0] not in chosen]})
    bench = bench_sample([r["ethAddress"].lower() for r in big])
    track = update_track(track, today, lbmap, picks, passing, bench)
    past = []
    for c in track.get("cohorts", []):   # ritorno dalla scelta a oggi per ogni scelta passata (prima apparizione)
        for x in c["picks"]:
            if x[0] in {p["address"] for p in past}:
                continue
            cur_v = lbmap.get(x[0])
            past.append({"address": x[0], "since": c["date"], "name": next((h[1] for hh in hist for h in hh["picks"] if h[0] == x[0]), x[0][:8]),
                         "ret": round(md_return(x[1], x[2], *cur_v), 4) if cur_v else None, "active": x[0] in chosen})
    out = {
        "version": VERSION, "ts": int(time.time()), "date": today, "level": level,
        "relaxed": [f"{k} → {v}" for k, v in RELAX[:level]], "thresholds": th, "weights": W,
        "picks": picks, "runners_up": runners,
        "scanned": {"leaderboard": len(rows), "leaderboard_1m": len(big), "vaults_1m": len(vinfo), "candidates": len(cands),
                    "analyzed": len(analyzed), "funding_checked": min(len(core), N_FUND), "passed": len(passing), "api_calls": api.calls,
                    "seconds": round(time.time() - t_start)},
        "prefilter_rejected": pre_rej, "rejected": rejected, "history": hist[-120:], "past": past[-30:],
        "track": track_summary(track), "changed": changed,
    }
    data_dir.mkdir(parents=True, exist_ok=True)
    (data_dir / PICKS).write_text(json.dumps(out, indent=1, default=str))
    (data_dir / TRACK).write_text(json.dumps(track, separators=(",", ":"), default=str))
    # candidati per la lista osservata: nessuna sostituzione automatica, l'utente approva via Telegram (/sostituisci)
    new_c = update_watch(watch, by, passing, today, entry, lambda a: _fills(api, a, now_ms))
    wallets.save_watch(watch, data_dir / WATCH)
    if new_c:
        msg = "\n\n".join(wallets.candidate_text(c) for c in new_c)
        if send and telegram.send(msg):
            for c in new_c:
                c["notified"] = today
            wallets.save_watch(watch, data_dir / WATCH)
        elif not send:
            log(msg)
    log(f"[scout] fatto in {time.time() - t_start:.0f} s · livello {level} · passano {len(passing)} · scelte: {[p['name'] for p in picks]}")
    return out


def summary(data_dir: Path = DATA) -> dict | None:
    """Versione compatta per report["scout"] (dashboard)."""
    d = _load(data_dir / PICKS, None)
    w = wallets.load_watch(data_dir / WATCH)
    watch = {k: w.get(k) for k in ("updated", "slots", "candidates", "review")}
    watch["history"] = (w.get("history") or [])[-10:]
    if not d:
        return {"watch": watch, "picks": [], "date": w.get("updated")}
    keep = ("version", "ts", "date", "level", "relaxed", "thresholds", "weights", "picks", "runners_up", "scanned", "rejected",
            "prefilter_rejected", "track", "past")
    s = {k: d.get(k) for k in keep}
    s["history"] = d.get("history", [])[-10:]
    s["watch"] = watch
    s["criteria"] = {"min_value": MIN_VALUE, "hist_days": HIST_DAYS, "perp_share": PERP_SHARE, "th0": TH0, "relax": RELAX, "margin": MARGIN}
    return s


def due(data_dir: Path = DATA, hours: float = EVERY_H) -> bool:
    d = _load(data_dir / PICKS, {})
    return time.time() - float(d.get("ts") or 0) >= hours * 3600


def daily(data_dir: Path = DATA) -> dict | None:
    """Chiamato da radar/cli.py ogni ora: gira solo se sono passate almeno 20 ore dall'ultimo giro."""
    if due(data_dir):
        try:
            run(data_dir)
        except Exception as e:  # noqa: BLE001
            print(f"[scout] giro non riuscito, resta la selezione precedente: {e!r}")
    return summary(data_dir)


if __name__ == "__main__":
    if "--force" in sys.argv or due():
        run(send="--no-telegram" not in sys.argv)
    else:
        print("[scout] ultimo giro meno di 20 ore fa: niente da fare (usa --force)")
    print(json.dumps((summary() or {}).get("picks", []), indent=1)[:2000])
