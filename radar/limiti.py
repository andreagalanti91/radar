"""Allarme "fuori dal backtest" di W3.2 (approvato dall'utente il 26/11/2026; solo avviso: non cambia segnali, stop, posizione
né capitale).

Un messaggio Telegram quando W3.2 dal vivo esce dai limiti visti nello storico:
  (a) calo del conto dal massimo oltre il peggiore storico (BTC: −21,1% dal 2021, memoria/01-strategia/RAPPORTO-W32.md);
  (b) perdite di fila oltre il massimo storico (BTC: 2, dal 2018);
  (c) una singola operazione che perde più della peggiore storica (BTC: −25,1%, gennaio 2018).
ETH ha limiti suoi, dal suo storico W3.2 dal 2021 (con i limiti di BTC l'avviso partirebbe dentro il comportamento normale
di ETH): calo −27,5%, 3 perdite di fila, peggiore −21,4% (weekly.evaluate su ETH, dati al 21/11/2026).

Si controlla sul conto del modello (report["weekly"]["history"]: equity eq1 dal 2021, trade chiusi e posizione aperta) e, quando
ci sono, sulle operazioni vere del diario (data/journal.json, radar/journal.py: conto = capitale dell'asset + risultati in $).
Solo eventi dal vivo: perdite e operazioni chiuse dall'avvio dal vivo dell'asset (weekly.ASSET_LIVE_START), calo misurato oggi.
Un avviso per evento (marcatore in data/state.json, chiave "limiti": scritto solo se Telegram conferma l'invio).
Diverso da radar/guard.py (soglia d'attenzione −15% e 2 stop dal vivo): qui il confine è il backtest stesso.
"""
from __future__ import annotations

import pandas as pd

from . import weekly

# limiti storici per asset: (calo dal massimo %, perdite di fila massime, peggiore operazione % sul capitale)
LIMITS = {"BTC": {"dd_pct": -21.1, "losses": 2, "trade_pct": -25.1,
                  "src": "storico BTC (calo dal 2021, perdite di fila e peggiore operazione dal 2018)"},
          "ETH": {"dd_pct": -27.5, "losses": 3, "trade_pct": -21.4, "src": "storico ETH dal 2021"}}
STATE_KEY = "limiti"


def _live(asset: str) -> str:
    return weekly.ASSET_LIVE_START.get(asset, weekly.LIVE_START)


def _streak(pnls: list[float]) -> int:
    n = 0
    for p in reversed(pnls):
        if p < 0:
            n += 1
        else:
            break
    return n


def model_check(w: dict | None, asset: str) -> dict:
    """Stato del conto del modello rispetto ai limiti: calo attuale dal massimo, perdite di fila, operazioni oltre la peggiore."""
    L, live = LIMITS[asset], _live(asset)
    h = (w or {}).get("history") or {}
    s = pd.Series(h.get("eq1") or [], index=pd.to_datetime(h.get("eq_dates") or []), dtype=float).dropna()
    out = {"dd_pct": None, "peak_date": None, "losses": 0, "last_loss": None, "bad_trades": [], "events": [], "why": []}
    if len(s):
        out["dd_pct"] = round(float((s.iloc[-1] / s.cummax().iloc[-1] - 1) * 100), 2)
        out["peak_date"] = str(s.idxmax().date())
    closed = [t for t in h.get("trades", []) if t.get("reason") != "open" and t.get("exit")]
    out["losses"] = _streak([t.get("pnl_pct") or 0 for t in closed])
    if out["losses"] and closed[-1]["exit"] >= live:
        out["last_loss"] = closed[-1]["signal"]
    if out["dd_pct"] is not None and out["dd_pct"] < L["dd_pct"]:
        out["events"].append(f"dd:{out['peak_date']}")
        out["why"].append(("dd", f"Calo del conto del modello dal massimo del {_dm(out['peak_date'])}: "
                                 f"{_pc(out['dd_pct'])} (peggiore storico {_pc(L['dd_pct'])})"))
    if out["losses"] > L["losses"] and out["last_loss"]:
        out["events"].append(f"losses:{out['last_loss']}")
        out["why"].append(("losses", f"Perdite di fila del modello: {out['losses']} (massimo storico {L['losses']})"))
    for t in h.get("trades", []):
        is_open = t.get("reason") == "open"
        if (is_open or (t.get("exit") or "") >= live) and (t.get("pnl_pct") or 0) < L["trade_pct"]:
            out["bad_trades"].append(t["signal"])
            out["events"].append(f"trade:{t['signal']}")
            out["why"].append(("trade", f"Operazione {t['side']} del segnale {_dm(t['signal'])}"
                                        f"{' (aperta)' if is_open else ''}: {_pc(t['pnl_pct'])} sul capitale "
                                        f"(peggiore storica {_pc(L['trade_pct'])})"))
    return out


def real_check(journal: dict | None, asset: str) -> dict:
    """Stesso controllo sulle operazioni vere W3.2 chiuse dell'asset (risultato in $ dal diario, sul capitale dell'asset)."""
    from .journal import asset_of, capital_of
    L, cap = LIMITS[asset], capital_of(asset)
    tr = [t for t in (journal or {}).get("trades", []) if t.get("strategy") in ("w2", "w3") and asset_of(t) == asset
          and t.get("exit") and t.get("pnl_usd") is not None]
    out = {"n": len(tr), "dd_pct": None, "losses": 0, "events": [], "why": []}
    if not tr or not cap:
        return out
    eq, peak, peak_id, pnls = cap, cap, None, []
    for t in tr:
        p = t["pnl_usd"] / eq * 100       # % sul conto all'ingresso, come nel backtest
        pnls.append(p)
        eq += t["pnl_usd"]
        if eq > peak:
            peak, peak_id = eq, t["id"]
        if p < L["trade_pct"]:
            out["events"].append(f"real_trade:{t['id']}")
            out["why"].append(("trade", f"Operazione vera {t['id']}: {_pc(p)} sul conto (peggiore storica {_pc(L['trade_pct'])})"))
    dd, pk = (eq / peak - 1) * 100, peak_id or "inizio"   # calo attuale dal massimo del conto vero
    out["dd_pct"], out["losses"] = round(dd, 2), _streak(pnls)
    if dd < L["dd_pct"]:
        out["events"].append(f"real_dd:{pk}")
        out["why"].append(("dd", f"Calo del conto vero dal massimo: {_pc(dd)} (peggiore storico {_pc(L['dd_pct'])})"))
    if out["losses"] > L["losses"]:
        out["events"].append(f"real_losses:{tr[-1]['id']}")
        out["why"].append(("losses", f"Perdite di fila delle operazioni vere: {out['losses']} (massimo storico {L['losses']})"))
    return out


def compute(w: dict | None, asset: str = "BTC", journal: dict | None = None) -> dict:
    m, r = model_check(w, asset), real_check(journal, asset)
    why = [x for _, x in m["why"]] + [x for _, x in r["why"]]
    return {"asset": asset, "limits": LIMITS[asset], "since": _live(asset), "model": m, "real": r,
            "events": m["events"] + r["events"], "why": why, "inside": not why}


def _pc(x: float) -> str:
    return f"{x:+.1f}%".replace(".", ",").replace("-", "−")


def _dm(d) -> str:
    try:
        return pd.Timestamp(d).strftime("%d/%m/%Y")
    except Exception:  # noqa: BLE001
        return str(d)


def page_line(g: dict | None) -> str:
    """Riga di stato della pagina Movimenti."""
    if not g:
        return "Limiti storici non calcolati in questo giro."
    if g["inside"]:
        m, L = g["model"], g["limits"]
        return (f"Dentro i limiti storici · calo {_pc(m['dd_pct'] or 0)} (limite {_pc(L['dd_pct'])}), perdite di fila "
                f"{m['losses']} (limite {L['losses']}), nessuna operazione oltre {_pc(L['trade_pct'])}")
    return "Fuori: " + "; ".join(g["why"])


def format_alarm(g: dict, new: list[str]) -> str:
    """Messaggio Telegram nel formato del bot: riga 1 = cosa succede, poi i numeri, dettagli richiudibili."""
    from . import telegram as tg
    kinds = {e.split(":")[0].removeprefix("real_") for e in new}
    what = {"dd": "calo oltre il peggiore del backtest", "losses": "troppe perdite di fila",
            "trade": "operazione peggiore del backtest"}
    first = " e ".join(what[k] for k in ("dd", "losses", "trade") if k in kinds) or "fuori dai limiti del backtest"
    L = g["limits"]
    return tg.msg(tg.head("🚨", g["asset"], f"W3.2 fuori dal backtest: {first}"),
                  *[f"• {tg.esc(x)}" for x in g["why"]],
                  f"Limiti storici: calo {tg.esc(_pc(L['dd_pct']))} · perdite di fila {L['losses']} · peggiore operazione "
                  f"{tg.esc(_pc(L['trade_pct']))}",
                  tg.details("Non è un ordine: è il segnale che la strategia sta uscendo dai suoi limiti storici; rivedere con calma.",
                             f"Limiti: {tg.esc(L['src'])}. Conto del modello: equity di W3.2 dal 2021 a 1x; operazioni vere: "
                             f"diario del bot dal {tg.dm(g['since'])}. Segnali, stop, posizione e capitale non cambiano."),
                  tg.foot())


def _view(g: dict) -> dict:
    return {k: g[k] for k in ("asset", "limits", "since", "inside", "why")} | {
        "line": page_line(g), "dd_pct": g["model"]["dd_pct"], "losses": g["model"]["losses"], "real_n": g["real"]["n"],
        "real_dd_pct": g["real"]["dd_pct"], "real_losses": g["real"]["losses"]}


def update(curs: dict, st: dict, journal: dict | None = None, send=None) -> dict:
    """curs = {"BTC": weekly.evaluate(...), "ETH": ...}. Per ogni asset calcola lo stato e invia un avviso con gli eventi nuovi;
    i marcatori (st["limiti"][asset]["sent"]) si scrivono solo se send conferma. Restituisce {asset: stato} per la pagina."""
    if send is None:
        from .telegram import send
    out = {}
    root = st.setdefault(STATE_KEY, {})
    for a, w in (curs or {}).items():
        if not w or a not in LIMITS:
            continue
        g = compute(w, a, journal)
        gs = root.setdefault(a, {})
        sent = list(gs.get("sent", []))
        new = [e for e in g["events"] if e not in sent]
        if new:
            if send(format_alarm(g, new)):
                gs["sent"] = (sent + new)[-30:]
                print(f"[limiti] {a} avviso inviato: {new}")
            else:
                print(f"[limiti] {a} avviso non confermato da Telegram: si riprova al prossimo giro")
        gs["last"] = {"inside": g["inside"], "dd_pct": g["model"]["dd_pct"], "losses": g["model"]["losses"]}
        out[a] = _view(g)
        print(f"[limiti] {a}: {out[a]['line']}")
    return out


def status(curs: dict, journal: dict | None = None) -> dict:
    """Solo calcolo, nessun invio né marcatore: per la dashboard quando il report non porta già "limiti"."""
    return {a: _view(compute(w, a, journal)) for a, w in (curs or {}).items() if w and a in LIMITS}
