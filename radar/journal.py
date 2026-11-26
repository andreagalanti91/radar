"""Registro dei trade reali via Telegram: l'utente scrive al bot cosa ha eseguito (Bybit/OKX), il workflow orario
legge i messaggi nuovi (getUpdates), salva in data/journal.json e risponde con una conferma breve.

Comandi (W3.2 su BTC ed ETH; v2 solo se scritto):
  /entrato <prezzo> [quantità] [btc|eth] [long|short] [comm <$>] [importo <$>] · ingresso eseguito
  /aggiungi <prezzo> [quantità] [comm <$>] · un altro pezzo dello stesso ingresso (ordine riempito in più volte)
  /uscito <prezzo> [quantità] [comm <$>] [motivo] · uscita (con una quantità minore di quella aperta: uscita parziale)
  /limit <prezzo> [quantità] · 2ª tranche di v2 (storico) · /exchange bybit|okx · /registro · /aiuto
  Asset: scritto (btc/eth) o dedotto dal prezzo (≥ 20.000 $ = BTC, sotto = ETH). Strategia: W3.2 se non scrivi v2.
         Wallet osservati (radar/wallets.py.command): /osservati · /candidati · /sostituisci <posto> <id> · /conferma <posto> · /scarta <id>
Si accettano solo i messaggi della chat TELEGRAM_CHAT_ID (gli altri si ignorano senza risposta). Offset di getUpdates in
data/state.json (chiave "tg_offset"). Il confronto col segnale (prezzo, slippage %, ritardo in ore) si completa con
link(report) dopo il calcolo del segnale: i giri di ricerca usano lo slippage reale misurato (RESEARCH.md).
"""
from __future__ import annotations

import json
import os
import re

import pandas as pd
import requests

from .data import DATA_DIR

JOURNAL_FILE = DATA_DIR / "journal.json"
STATE_FILE = DATA_DIR / "state.json"
EXCHANGE = "bybit/okx"
W_V2 = (0.4, 0.6)   # pesi delle due tranche di v2 se la quantità non è indicata

HELP = ("📒 <b>Diario delle operazioni vere · W3.2 su BTC ed ETH</b>\n"
        "/entrato 65150 0,45 btc comm 14,7 · ingresso eseguito: prezzo, quantità (BTC o ETH), commissioni in $\n"
        "/entrato 2150 importo 29000 eth · in alternativa alla quantità, l'importo in $\n"
        "/aggiungi 65300 0,05 comm 1,6 · altro pezzo dello stesso ingresso\n"
        "/uscito 59800 btc comm 13,5 · uscita (con una quantità minore di quella aperta: uscita parziale)\n"
        "/registro · ultime operazioni vere contro il modello · /exchange bybit|okx\n"
        "Asset, lato e segnale si deducono se non li scrivi (BTC se il prezzo è ≥ 20.000 $, altrimenti ETH). "
        "Commissioni: il totale in $ dell'eseguito (funding incluso, se vuoi). Virgola o punto vanno bene.\n"
        "Confronto con il modello e slittamento: al giro dopo, e nella pagina Movimenti («Reale contro modello»).\n"
        "Post di un trader: inoltra il post X o lo screenshot · /trade long 73200 stop 72100 tp 77600 · /trader riepilogo\n"
        "Il bot legge i messaggi a ogni giro orario: la risposta arriva entro un'ora.")
ASSETS = ("BTC", "ETH")
ETH_MAX = 20000.0   # prezzo sotto il quale, senza asset scritto, l'operazione è su ETH
FEE_WORDS = ("comm", "commissione", "commissioni", "fee", "fees")
AMOUNT_WORDS = ("importo", "usd", "usdt", "dollari")


# ---------------------------------------------------------------- file

def _read(path, default):
    try:
        return json.loads(path.read_text())
    except (OSError, ValueError):
        return default


def load() -> dict:
    j = _read(JOURNAL_FILE, {})
    j.setdefault("exchange", EXCHANGE)
    j.setdefault("trades", [])
    j.setdefault("ref", {})
    return j


def save(j: dict) -> None:
    JOURNAL_FILE.write_text(json.dumps(j, indent=1, default=str))


# ---------------------------------------------------------------- parsing

def num(s: str, price: bool = True) -> float | None:
    """'67.500' / '67,500' / '67500,5' / '67.500,5' -> float. Con un solo separatore seguito da 3 cifre, per i prezzi
    è il separatore delle migliaia (67.500 = 67500); per le quantità è sempre il decimale (0,015)."""
    s = s.strip().replace("$", "").replace("'", "").replace(" ", "")
    if not re.fullmatch(r"\d[\d.,]*", s):
        return None
    if "." in s and "," in s:   # l'ultimo separatore è il decimale
        dec = "." if s.rfind(".") > s.rfind(",") else ","
        s = s.replace("," if dec == "." else ".", "").replace(dec, ".")
    elif s.count(".") + s.count(",") > 1:   # 1.234.567: solo migliaia
        s = s.replace(".", "").replace(",", "")
    elif "." in s or "," in s:
        a, b = re.split(r"[.,]", s)
        s = a + b if (price and len(b) == 3 and a != "0") else a + "." + b
    try:
        return float(s)
    except ValueError:
        return None


def parse(text: str) -> tuple[str, dict]:
    """Testo del messaggio -> (comando, argomenti): prezzo, quantità, strategia, lato, asset, commissioni e importo in $."""
    parts = text.strip().split()
    if not parts or not parts[0].startswith("/"):
        return "", {}
    cmd = parts[0][1:].split("@")[0].lower()
    args = {"nums": [], "strategy": None, "side": None, "asset": None, "fee": None, "amount": None, "words": []}
    key = None
    for p in parts[1:]:
        w = p.lower().rstrip(":")
        if key:   # valore di "comm" / "importo"
            v = num(w)
            if v is not None:
                args[key] = v
                key = None
                continue
            key = None
        if w in FEE_WORDS:
            key = "fee"
        elif w in AMOUNT_WORDS:
            key = "amount"
        elif w in ("v2", "w2", "w3", "w32", "w3.2", "w3,2"):
            args["strategy"] = "v2" if w == "v2" else "w2"   # "w2" = chiave storica di W3.2 nel registro
        elif w in ("long", "short"):
            args["side"] = w
        elif w in ("btc", "eth"):
            args["asset"] = w.upper()
        elif w == "x":
            continue
        elif num(w) is not None and len(args["nums"]) < 2:
            args["nums"].append(w)
        else:
            args["words"].append(p)
    raw = args.pop("nums")
    args["price"] = num(raw[0]) if raw else None
    args["qty"] = num(raw[1], price=False) if len(raw) > 1 else None
    if args["qty"] is None and args["amount"] and args["price"]:
        args["qty"] = round(args["amount"] / args["price"], 6)
    return cmd, args


# ---------------------------------------------------------------- calcoli

def _usd(x: float | None) -> str:
    return "–" if x is None else f"${x:,.0f}".replace(",", ".")


def _px(x: float | None) -> str:
    """Prezzo: senza decimali da 10.000 $ in su (BTC), con due sotto (ETH)."""
    if x is None:
        return "–"
    return _usd(x) if abs(x) >= 10000 else _usd2(x)


def _usd2(x: float) -> str:
    return f"${x:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def _sdusd(x: float | None) -> str:
    return "–" if x is None else ("+" if x >= 0 else "−") + _usd(abs(x))


def asset_of(t: dict) -> str:
    return t.get("asset") or "BTC"   # trade registrati prima di ETH: BTC


def label(t: dict) -> str:
    return "W3.2" if t.get("strategy") in ("w2", "w3") else str(t.get("strategy", "")).upper()


def _avg(t: dict) -> float:
    e = t["entries"]
    if all(x.get("qty") for x in e):
        w = [x["qty"] for x in e]
    elif t["strategy"] == "v2" and len(e) == 2:
        w = list(W_V2)
    else:
        w = [1.0] * len(e)
    return sum(x["price"] * k for x, k in zip(e, w)) / sum(w)


def qty_in(t: dict) -> float | None:
    """Quantità entrata (None se un pezzo non ha la quantità)."""
    q = [x.get("qty") for x in t["entries"]]
    return round(sum(q), 8) if q and all(q) else None


def qty_out(t: dict) -> float:
    return round(sum(x.get("qty") or 0 for x in t.get("exits") or []), 8)


def fees(t: dict) -> float:
    return round(sum(x.get("fee") or 0 for x in t["entries"] + (t.get("exits") or [])), 2)


def _hours(a: str | None, b: str | None) -> float | None:
    if not a or not b:
        return None
    return round((pd.Timestamp(a) - pd.Timestamp(b)).total_seconds() / 3600, 1)


def _slip(real: float, sig: float | None, side: str, entry: bool) -> float | None:
    """Slippage in % rispetto al segnale: positivo = peggio del segnale (long: comprato più caro / venduto più basso)."""
    if not sig:
        return None
    s = (real - sig) / sig * 100 * (1 if side == "long" else -1) * (1 if entry else -1)
    return round(s, 3)


def _exit_avg(t: dict) -> float | None:
    xs = t.get("exits") or []
    if not xs:
        return None
    if all(x.get("qty") for x in xs):
        return sum(x["price"] * x["qty"] for x in xs) / sum(x["qty"] for x in xs)
    return xs[-1]["price"]


def model_fee_rate(t: dict) -> float:
    """Commissione per lato del modello: long in spot (0,1%), short in perp (0,05%) (radar/weekly.py)."""
    from .weekly import FEE_PERP, FEE_SPOT
    mk = (t.get("signal") or {}).get("market")
    return FEE_SPOT if (mk == "spot" or (mk is None and t["side"] == "long")) else FEE_PERP


def compare(t: dict) -> dict:
    """Ricalcola medio, risultato % sul prezzo, risultato in $ (con quantità e commissioni) e confronto col segnale
    (slippage %, ritardo in ore). Per W3.2: lo stesso risultato col prezzo del modello e la stessa quantità ("model_usd")
    e l'effetto dell'esecuzione reale (real − modello): positivo = l'esecuzione ha aggiunto."""
    t.setdefault("exits", [t["exit"]] if t.get("exit") else [])
    sig = t.get("signal") or {}
    sg = 1 if t["side"] == "long" else -1
    t["avg"] = round(_avg(t), 2)
    t["qty"] = qty_in(t)
    t["fees"] = fees(t)
    e0 = t["entries"][0]
    c = {"slip_entry_pct": _slip(t["avg"] if t["strategy"] != "v2" else e0["price"], sig.get("entry"), t["side"], True),
         "delay_entry_h": _hours(e0["time"], sig.get("entry_time"))}
    lim = next((x for x in t["entries"][1:] if x.get("kind") == "limit"), None)
    if lim and sig.get("limit"):
        c["slip_limit_pct"] = _slip(lim["price"], sig["limit"], t["side"], True)
    q, fr = t["qty"], model_fee_rate(t)
    if q and sig.get("entry"):
        c["entry_effect_usd"] = round(sg * q * (sig["entry"] - t["avg"]) - (sum(x.get("fee") or 0 for x in t["entries"])
                                                                              - q * sig["entry"] * fr), 2)
    xa = _exit_avg(t)
    if xa is not None:
        qo = qty_out(t) if all(x.get("qty") for x in t["exits"]) else q
        t["exit_avg"] = round(xa, 2)
        if qo:
            t["pnl_usd"] = round(sg * qo * (xa - t["avg"]) - t["fees"], 2)
    if t.get("exit"):
        x = t["exit"]
        t["result_pct"] = round((xa / t["avg"] - 1) * 100 * sg, 2)
        c["slip_exit_pct"] = _slip(xa, sig.get("exit"), t["side"], False)
        c["delay_exit_h"] = _hours(x["time"], sig.get("exit_time"))
        if sig.get("result_pct") is not None:
            c["result_vs_signal_pct"] = round(t["result_pct"] - sig["result_pct"], 2)
        if q and sig.get("entry") and sig.get("exit"):
            m = sg * q * (sig["exit"] - sig["entry"]) - q * (sig["entry"] + sig["exit"]) * fr
            t["model_usd"] = round(m, 2)
            if t.get("pnl_usd") is not None:
                c["effect_usd"] = round(t["pnl_usd"] - m, 2)
    t["compare"] = c
    return t


def averages(j: dict) -> dict:
    """Slippage e ritardo medi sui trade reali (None se non ci sono dati)."""
    def m(k):
        v = [t["compare"][k] for t in j["trades"] if t.get("compare", {}).get(k) is not None]
        return round(sum(v) / len(v), 3) if v else None
    slips = [t["compare"][k] for t in j["trades"] for k in ("slip_entry_pct", "slip_limit_pct", "slip_exit_pct")
             if t.get("compare", {}).get(k) is not None]
    return {"n": len(j["trades"]), "closed": sum(1 for t in j["trades"] if t.get("exit")),
            "slip_pct": round(sum(slips) / len(slips), 3) if slips else None,
            "slip_entry_pct": m("slip_entry_pct"), "slip_exit_pct": m("slip_exit_pct"),
            "delay_entry_h": m("delay_entry_h"), "delay_exit_h": m("delay_exit_h")}


def capital_of(asset: str) -> float:
    from .weekly import asset_capital
    return asset_capital(asset)


def real_vs_model(j: dict) -> dict:
    """Vista "Reale contro modello" (pagina Movimenti): per ogni operazione vera di W3.2 prezzo e data del segnale contro
    l'eseguito, slittamento, risultato reale contro quello del modello alla stessa quantità, effetto dell'esecuzione; totale
    in $ e in % del capitale dell'asset. Le aperte contano solo per l'ingresso (l'uscita non c'è ancora)."""
    rows, tot, tot_c, n_eff = [], 0.0, 0.0, 0
    for t in j.get("trades", []):
        if t.get("strategy") not in ("w2", "w3"):
            continue
        sig, c, a = t.get("signal") or {}, t.get("compare") or {}, asset_of(t)
        cap = capital_of(a)
        closed = bool(t.get("exit"))
        eff = c.get("effect_usd") if closed else c.get("entry_effect_usd")
        fr = model_fee_rate(t) * 100
        model_pct = (round((sig["exit"] / sig["entry"] - 1) * 100 * (1 if t["side"] == "long" else -1) - 2 * fr, 2)
                     if closed and sig.get("entry") and sig.get("exit") else None)
        notional = (t.get("qty") or 0) * t["avg"]
        real_pct = (round(t["pnl_usd"] / notional * 100, 2) if closed and t.get("pnl_usd") is not None and notional
                    else (t.get("result_pct") if closed else None))
        r = {"id": t["id"], "asset": a, "side": t["side"], "signal_date": t.get("signal_date"), "closed": closed,
             "model_entry": sig.get("entry"), "model_entry_time": sig.get("entry_time"),
             "real_entry": t["avg"], "real_entry_time": t["entries"][0]["time"], "slip_entry_pct": c.get("slip_entry_pct"),
             "model_exit": sig.get("exit"), "model_exit_time": sig.get("exit_time"),
             "real_exit": t.get("exit_avg") if closed else None, "real_exit_time": (t.get("exit") or {}).get("time"),
             "slip_exit_pct": c.get("slip_exit_pct"), "qty": t.get("qty"), "fees": t.get("fees"),
             "real_pct": real_pct, "model_pct": model_pct, "real_usd": t.get("pnl_usd") if closed else None,
             "model_usd": t.get("model_usd") if closed else None, "effect_usd": eff,
             "partial_out": qty_out(t) if (not closed and t.get("exits")) else None,
             "real_cap_pct": round(t["pnl_usd"] / cap * 100, 2) if closed and t.get("pnl_usd") is not None and cap else None}
        rows.append(r)
        if eff is not None:
            tot += eff
            tot_c += eff / cap * 100 if cap else 0
            n_eff += 1
    return {"rows": rows, "n": len(rows), "closed": sum(1 for r in rows if r["closed"]), "n_effect": n_eff,
            "effect_usd": round(tot, 2) if n_eff else None, "effect_cap_pct": round(tot_c, 3) if n_eff else None,
            "help": "/entrato 65150 0,45 btc comm 14,7 · /uscito 59800 btc comm 13,5 · /registro"}


# ---------------------------------------------------------------- segnale attivo

def _active(state: dict) -> dict:
    """Segnali attivi da data/state.json: {'v2': (lato, data), 'w2': (lato, data) di BTC, 'w2_eth': (...) di ETH}."""
    out = {}
    v = state.get("v2") or {}
    if v.get("status") in ("conferma", "ingresso", "aperto") and v.get("side"):
        out["v2"] = (v["side"], v.get("signal_date"))
    for a in ASSETS:
        w = state.get(_wkey(a)) or {}
        if w.get("status") in ("segnale", "aperto", "uscita") and w.get("side"):
            out[_rkey("w2", a)] = (w["side"], w.get("signal_date"))
    return out


def _wkey(asset: str) -> str:
    return "weekly" if asset == "BTC" else f"weekly_{asset.lower()}"


def _rkey(strategy: str, asset: str) -> str:
    """Chiave del riferimento in j["ref"]: "v2", "w2" (W3.2 BTC, chiave storica), "w2_eth"."""
    return strategy if strategy == "v2" or asset == "BTC" else f"{strategy}_{asset.lower()}"


def _guess_asset(a: dict) -> str:
    if a.get("asset"):
        return a["asset"]
    return "ETH" if a.get("price") and a["price"] < ETH_MAX else "BTC"


def _open(j: dict, strategy: str | None, asset: str | None = None) -> list[dict]:
    return [t for t in j["trades"] if not t.get("exit") and (strategy is None or t["strategy"] == strategy)
            and (asset is None or asset_of(t) == asset)]


def _pct(x: float | None, d: int = 2) -> str:
    return "–" if x is None else f"{x:+.{d}f}%".replace(".", ",").replace("-", "−")


def _h(x: float | None) -> str:
    return "–" if x is None else f"{x:.1f}".replace(".", ",")


def _q(x: float | None) -> str:
    return "" if not x else f"{x:.6f}".rstrip("0").rstrip(".").replace(".", ",")


def _cmp_text(t: dict) -> str:
    c, sig = t.get("compare", {}), t.get("signal") or {}
    w3 = t.get("strategy") in ("w2", "w3")
    lab = "modello" if w3 else "Segnale"
    if c.get("slip_exit_pct") is not None or c.get("delay_exit_h") is not None:
        out = (f"{'Uscita del modello' if w3 else 'Segnale uscita'} {_px(sig.get('exit'))} · slittamento "
               f"{_pct(c.get('slip_exit_pct'), 3)} · ritardo {_h(c.get('delay_exit_h'))} h")
        if c.get("effect_usd") is not None:
            out += (f"\nRisultato {_sdusd(t.get('pnl_usd'))} contro {_sdusd(t.get('model_usd'))} del modello alla stessa "
                    f"quantità: l'esecuzione ha {'aggiunto' if c['effect_usd'] >= 0 else 'tolto'} {_usd(abs(c['effect_usd']))}")
        return out
    if c.get("slip_entry_pct") is not None:
        return (f"{'Ingresso del modello' if w3 else lab + ' ingresso'} {_px(sig.get('entry'))} · slittamento "
                f"{_pct(c['slip_entry_pct'], 3)} · ritardo {_h(c.get('delay_entry_h'))} h")
    return "Confronto col modello al prossimo giro orario (dopo l'apertura del lunedì)." if w3 else \
        "Confronto col segnale al prossimo giro orario."


def _fill(a: dict, when: str, kind: str) -> dict:
    return {"price": a["price"], "qty": a["qty"], "fee": a.get("fee"), "time": when, "kind": kind}


# ---------------------------------------------------------------- comandi

def handle(text: str, when: str, j: dict, state: dict) -> str:
    """Esegue un comando sul registro j (modificato sul posto) e restituisce la risposta (HTML di Telegram)."""
    from . import wallets   # lista dei 3 wallet osservati: /osservati /candidati /sostituisci /conferma /scarta
    w = wallets.command(text, when[:10])
    if w is not None:
        return w
    from . import xinbox   # trader seguito: /trade /trader
    x = xinbox.command(text, when)
    if x is not None:
        return x
    from .telegram import esc
    cmd, a = parse(text)
    if cmd in ("aiuto", "help", "start", "diario"):
        return HELP + "\n\n" + (wallets.HELP_W if wallets.enabled() else "<b>Wallet osservati</b>: " + wallets.PAUSED)
    if cmd == "exchange":
        ex = next((w.lower() for w in a["words"] if w.lower() in ("bybit", "okx")), None)
        if not ex:
            return "Scrivi /exchange bybit oppure /exchange okx."
        j["exchange"] = ex
        for t in _open(j, None):
            t["exchange"] = ex
        return f"Exchange impostato: {ex} (trade aperti e prossimi)."
    if cmd == "registro":
        return summary(j)
    if cmd == "entrato":
        if not a["price"]:
            return "Manca il prezzo: /entrato 65150 0,45 btc comm 14,7"
        act = _active(state)
        strat = a["strategy"] or "w2"   # W3.2 se non scritto (v2 è spenta dal 12/11/2026: solo se scritta)
        asset = "BTC" if strat == "v2" else _guess_asset(a)
        rk = _rkey(strat, asset)
        side = a["side"] or (act.get(rk) or (None,))[0]
        if not side:
            return (f"Nessun segnale {label({'strategy': strat})} {asset} attivo: specifica il lato, es. "
                    f"/entrato {a['price']:.0f} {asset.lower()} {strat} long")
        sd = act[rk][1] if rk in act and act[rk][0] == side else None
        ref = j["ref"].get(rk) or {}
        sig = {k: ref.get(k) for k in ("entry", "entry_time", "limit", "market")} if ref.get("signal_date") == sd and sd else {}
        n = sum(1 for t in j["trades"] if t["id"].startswith(when[:10])) + 1
        t = {"id": f"{when[:10]}-{n}", "strategy": strat, "asset": asset, "side": side, "exchange": j["exchange"],
             "signal_date": sd, "entries": [_fill(a, when, "ingresso")], "exits": [], "exit": None,
             "result_pct": None, "signal": sig, "note": " ".join(a["words"]) or None}
        j["trades"].append(compare(t))
        q = f" · {_q(a['qty'])} {asset}" if a["qty"] else ""
        imp = f" = {_usd(a['qty'] * a['price'])}" if a["qty"] else ""
        fee = f" · commissioni {_usd2(a['fee'])}" if a.get("fee") else ""
        warn = "" if sd or strat == "v2" else "\nNessun segnale W3.2 attivo con questo lato: registrata, senza confronto col modello."
        return (f"✅ Registrato ingresso {side} {label(t)} {asset} a {_px(a['price'])}{q}{imp}{fee} ({esc(t['exchange'])}) · "
                f"id {t['id']}\n" + _cmp_text(t) + warn)
    if cmd in ("limit", "aggiungi", "uscito"):
        if not a["price"]:
            return f"Manca il prezzo: /{cmd} 59800" + (" [quantità] [comm 13,5] [motivo]" if cmd == "uscito" else " [quantità]")
        asset = a["asset"] or (None if a["strategy"] == "v2" else _guess_asset(a))
        op_all = _open(j, a["strategy"])
        op = [t for t in op_all if asset is None or t["strategy"] == "v2" or asset_of(t) == asset]
        if not op_all:
            return "Nessun trade reale aperto: registra prima l'ingresso con /entrato."
        if not op:
            return (f"Nessun trade {asset} aperto (aperti: {', '.join(label(t) + ' ' + asset_of(t) for t in op_all)}): "
                    f"controlla il prezzo o scrivi l'asset, es. /{cmd} {a['price']:.0f} {asset_of(op_all[0]).lower()}")
        if len(op) > 1:
            return (f"Più trade aperti ({', '.join(label(t) + ' ' + asset_of(t) for t in op)}): specifica, es. "
                    f"/{cmd} {a['price']:.0f} eth")
        t = op[0]
        if cmd in ("limit", "aggiungi"):
            t["entries"].append(_fill(a, when, "limit" if cmd == "limit" else "aggiunta"))
            compare(t)
            return (f"✅ {'Limit eseguito' if cmd == 'limit' else 'Aggiunto all’ingresso'} a {_px(a['price'])} · medio "
                    f"{_px(t['avg'])}" + (f" · totale {_q(t['qty'])} {asset_of(t)}" if t.get("qty") else "")
                    + f" ({label(t)} {asset_of(t)} {t['side']})"
                    + (f"\nSegnale limit {_usd(t['signal']['limit'])} · slippage {_pct(t['compare']['slip_limit_pct'], 3)}"
                       if t["compare"].get("slip_limit_pct") is not None else ""))
        fill = _fill(a, when, "uscita")
        fill["reason"] = " ".join(a["words"]) or None
        t.setdefault("exits", []).append(fill)
        qi, left = t.get("qty"), None
        if qi and a["qty"] and all(x.get("qty") for x in t["exits"]):
            left = round(qi - qty_out(t), 8)
        if left is not None and left > qi * 1e-4:
            compare(t)
            return (f"✅ Uscita parziale {label(t)} {asset_of(t)} a {_px(a['price'])} · {_q(a['qty'])} {asset_of(t)}; "
                    f"restano aperti {_q(left)} {asset_of(t)}. Per chiudere: /uscito &lt;prezzo&gt; {_q(left)} {asset_of(t).lower()}")
        t["exit"] = {"price": round(_exit_avg(t), 2), "time": when, "reason": fill["reason"]}
        compare(t)
        cap = capital_of(asset_of(t)) if t["strategy"] != "v2" else None
        res = (f" · {_sdusd(t['pnl_usd'])}" + (f" ({_pct(t['pnl_usd'] / cap * 100)} sul capitale {asset_of(t)})" if cap else "")
               if t.get("pnl_usd") is not None else "")
        return (f"✅ Uscita {label(t)} {asset_of(t) if t['strategy'] != 'v2' else ''} {t['side']} a {_px(t['exit']['price'])} · "
                f"medio {_px(t['avg'])} · risultato {_pct(t['result_pct'])} sul prezzo{res}\n".replace("  ", " ") + _cmp_text(t))
    return "Comando non riconosciuto. Scrivi /aiuto per l'elenco."


def summary(j: dict, n: int = 5) -> str:
    if not j["trades"]:
        return "Registro vuoto: nessun trade reale. Scrivi /aiuto per i comandi."
    lines = ["📒 <b>Diario delle operazioni vere</b>"]
    for t in j["trades"][-n:][::-1]:
        c = t.get("compare", {})
        st = (f"uscita {_px(t['exit']['price'])} · {_pct(t['result_pct'])}" + (f" · {_sdusd(t['pnl_usd'])}" if t.get("pnl_usd") is not None else "")
              if t.get("exit") else "aperto")
        lines.append(f"{t['id']} · {label(t)} {asset_of(t)} {t['side']} · medio {_px(t['avg'])} · {st} · "
                     f"slittamento ingresso {_pct(c.get('slip_entry_pct'), 3)}, ritardo {_h(c.get('delay_entry_h'))} h"
                     + (f" · esecuzione {_sdusd(c['effect_usd'])}" if c.get("effect_usd") is not None else ""))
    m = averages(j)
    lines.append(f"Medie su {m['n']} trade ({m['closed']} chiusi): slippage {_pct(m['slip_pct'], 3)} · ritardo ingresso "
                 f"{_h(m['delay_entry_h'])} h (slippage positivo = peggio del segnale)")
    rv = real_vs_model(j)
    if rv["effect_usd"] is not None:
        lines.append(f"Esecuzione reale contro modello (W3.2, {rv['n_effect']} operazioni): {_sdusd(rv['effect_usd'])}")
    return "\n".join(lines)


# ---------------------------------------------------------------- Telegram

def _api(method: str, **kw) -> dict:
    token = os.environ.get("TELEGRAM_BOT_TOKEN")
    r = requests.post(f"https://api.telegram.org/bot{token}/{method}", json=kw, timeout=20)
    return r.json() if r.ok else {"ok": False, "description": r.text}


def poll() -> int:
    """Legge i messaggi nuovi del bot, esegue i comandi della chat TELEGRAM_CHAT_ID e risponde. Restituisce il numero di
    comandi eseguiti. Senza token/chat non fa nulla."""
    token, chat = os.environ.get("TELEGRAM_BOT_TOKEN"), os.environ.get("TELEGRAM_CHAT_ID")
    if not token or not chat:
        return 0
    state = _read(STATE_FILE, {})
    res = _api("getUpdates", offset=state.get("tg_offset", 0), timeout=2, allowed_updates=["message"])
    if not res.get("ok"):
        print(f"[journal] getUpdates non riuscito: {res.get('description')}")
        return 0
    ups = res.get("result", [])
    if not ups:
        return 0
    j, done = load(), 0
    for u in ups:
        m = u.get("message") or {}
        if str((m.get("chat") or {}).get("id")) != str(chat):
            continue   # altre chat: ignorate, nessuna risposta
        when = str(pd.Timestamp(m.get("date", 0), unit="s"))
        if not m.get("text", "").startswith("/"):
            txt = m.get("text") or m.get("caption") or ""
            if not (m.get("photo") or m.get("forward_origin") or re.search(r"https?://(?:x|twitter)\.com/", txt)):
                continue   # testo libero senza post allegato: ignorato, nessuna risposta
            # post del trader seguito inoltrati dall'utente (link X, testo, screenshot): radar/xinbox.py
            from . import xinbox
            try:
                reply = xinbox.ingest(m, _api)
            except Exception as e:  # noqa: BLE001
                reply = f"Post non salvato ({type(e).__name__})."
            _api("sendMessage", chat_id=chat, text=reply, parse_mode="HTML", reply_to_message_id=m.get("message_id"))
            done += 1
            continue
        try:
            reply = handle(m["text"], when, j, state)
        except Exception as e:  # noqa: BLE001  un comando malformato non deve bloccare l'offset
            reply = f"Comando non registrato ({type(e).__name__}). Scrivi /aiuto per il formato."
        _api("sendMessage", chat_id=chat, text=reply, parse_mode="HTML", reply_to_message_id=m.get("message_id"))
        done += 1
    if done:
        save(j)
    state = _read(STATE_FILE, {})   # rilettura: lo stato potrebbe essere cambiato
    state["tg_offset"] = max(u["update_id"] for u in ups) + 1
    STATE_FILE.write_text(json.dumps(state, indent=2, default=str))
    return done


# ---------------------------------------------------------------- confronto col segnale

MATCH_DAYS = 7   # senza data del segnale: si aggancia l'operazione del modello con lo stesso lato entrata entro 7 giorni


def _w3_sig(x: dict) -> dict:
    """Riferimento del modello da un trade dello storico di W3.2 (weekly.evaluate: history.trades)."""
    s = {"entry": x.get("entry_px"), "entry_time": x.get("entry"), "market": x.get("market"), "expo": x.get("expo")}
    if x.get("reason") != "open" and x.get("exit_px"):
        s.update(exit=x["exit_px"], exit_time=x.get("exit"), exit_kind=x.get("reason"), result_pct=x.get("move_pct"),
                 pnl_cap_pct=x.get("pnl_pct"))
    return s


def link(report: dict) -> None:
    """Dopo il calcolo del segnale: salva il riferimento attuale (v2, W3.2 BTC ed ETH) e completa il confronto dei trade
    reali con i prezzi e gli orari del modello (ingresso, limit, uscita, risultato)."""
    j = load()
    ref = {}
    v = report.get("v2") or {}
    if v.get("status") in ("conferma", "ingresso", "aperto"):
        p = v.get("plan") or {}
        ref["v2"] = {"signal_date": v.get("signal_date"), "side": v.get("side"),
                     "entry": v.get("entry") or v.get("entry_est") or p.get("entry"), "entry_time": v.get("entry_time"),
                     "limit": (v.get("levels") or [None, p.get("limit")])[1]}
    hist = {}
    for a, k in (("BTC", "weekly"), ("ETH", "weekly_eth")):
        w = report.get(k) or {}
        if w.get("status") in ("aperto", "uscita"):
            ref[_rkey("w2", a)] = {"signal_date": w.get("signal_date"), "side": w.get("side"), "entry": w.get("entry_px"),
                                   "entry_time": w.get("entry"), "limit": None, "market": w.get("market")}
        hist[a] = (w.get("history") or {}).get("trades") or []
    j["ref"] = ref
    v2 = {t["signal_date"]: t for t in (report.get("trades") or {}).get("futures", [])}
    for t in j["trades"]:
        sd, s = t.get("signal_date"), dict(t.get("signal") or {})
        if t["strategy"] in ("w2", "w3"):
            h = hist.get(asset_of(t)) or []
            x = next((x for x in h if sd and x.get("signal") == sd), None)
            if x is None and not sd and h:   # registrata senza segnale attivo: operazione del modello più vicina, stesso lato
                e0 = pd.Timestamp(t["entries"][0]["time"])
                near = [x for x in h if x.get("side") == t["side"] and x.get("entry")
                        and abs((pd.Timestamp(x["entry"]) - e0).days) <= MATCH_DAYS]
                x = min(near, key=lambda x: abs(pd.Timestamp(x["entry"]) - e0), default=None)
                if x is not None:
                    t["signal_date"] = x["signal"]
            if x is not None:
                s.update(_w3_sig(x))
            elif sd and sd == (ref.get(_rkey("w2", asset_of(t))) or {}).get("signal_date"):
                s.update({k: ref[_rkey("w2", asset_of(t))][k] for k in ("entry", "entry_time", "market")})
            if not h and not s:
                continue
        elif not sd:
            continue
        elif t["strategy"] == "v2" and sd in v2:
            x = v2[sd]
            s.update(entry=x.get("entry"), entry_time=x.get("entry_time"), limit=(x.get("levels") or [None, None])[1])
            if x.get("exit") != "open":
                s.update(exit=x.get("exit_px"), exit_time=x.get("exit_time") or x.get("exit_date"), exit_kind=x.get("exit"),
                         result_pct=x.get("pnl_pct_invested"))
        elif sd == (ref.get(t["strategy"]) or {}).get("signal_date"):
            s.update({k: ref[t["strategy"]][k] for k in ("entry", "entry_time", "limit")})
        t["signal"] = s
        compare(t)
    save(j)
