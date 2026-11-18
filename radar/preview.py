"""Pre-analisi della prossima decisione W3 (chiusura UTC della domenica), con i dati di oggi.

Non cambia W3: proietta la settimana in corso come se chiudesse al prezzo C (candele giornaliere chiuse + giorni mancanti
fino a domenica a C) e la passa a weekly.weekly_bars / weekly._decide, cioè alle stesse regole del segnale vero.
Le soglie di prezzo che cambiano l'esito sono in forma chiusa (le medie della settimana proiettata sono lineari in C):
- chiusura sotto/sopra la SMA40 proiettata: C < S39/39 (S39 = somma delle ultime 39 chiusure settimanali);
- SMA40 in calo su 4 settimane: (S39 + C)/40 < SMA40 di 4 settimane prima;
- EMA20 in calo/salita e chiusura oltre la EMA21: EMA(C) = a·C + (1−a)·EMA_prec, quindi la soglia è la EMA precedente;
- filtro F1/MACD: MACD(C) lineare in C; MACD > segnale ⇔ MACD(C) > segnale precedente.
Il flusso perp proiettato è quello attuale (live_flow): a domenica la media userà i giorni fino al sabato.
Statistiche di contesto sulle liquidazioni: tabella fissa in research/preview/liq_context.json (non si ricalcolano).
"position_block": la posizione W3 aperta (o in apertura lunedì) con PnL sul capitale, stop, soglia d'uscita EMA21 e distribuzione.
"today": quadro del giorno (flussi, derivati, liquidazioni, medie, S/R, cella storica più vicina) con l'affidabilità dimostrata
dagli studi: tabelle fisse dello studio N4 (research/preview/analog.json, sr_hold.json). Contesto, non segnale: decide W3.
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import weekly as W

LIQ_CONTEXT = Path(__file__).resolve().parent.parent / "research" / "preview" / "liq_context.json"
ANALOG = LIQ_CONTEXT.parent / "analog.json"      # N4: P(r>0) per celle pf14z × sf14z a terzili (research/preview/n4_tables.py)
SR_HOLD = LIQ_CONTEXT.parent / "sr_hold.json"    # N4: tenuta storica dei livelli S/R contro livelli casuali
TODAY_NOTE = "Contesto, non segnale: decide W3."
NOTE = "Stima con i dati di oggi: decide solo la chiusura di domenica (UTC)."
NEED = ("open", "high", "low", "close", "pf14z", "funding")


def _usd(x: float | None) -> str:
    return "—" if x is None else f"{x:,.0f} $".replace(",", ".")


def _sig(x: float) -> str:
    return f"{x:+.2f}σ".replace(".", ",").replace("-", "−")


def _week_close(last: pd.Timestamp) -> pd.Timestamp:
    """Domenica della prossima decisione: quella della settimana in corso (la successiva se i dati arrivano a domenica)."""
    return last + pd.Timedelta(days=(6 - last.dayofweek) or 7)


def project(f: pd.DataFrame, C: float, flow: float | None = None) -> pd.DataFrame:
    """Dati giornalieri con la settimana in corso completata fino a domenica al prezzo C (open=high=low=close=C nei giorni
    mancanti, funding ripetuto). pf14z dei giorni mancanti scelto in modo che il flusso della domenica (live_flow) valga
    `flow` (se None: il flusso attuale); se i giorni del flusso sono già tutti nei dati resta quello dei dati."""
    f = f[f["close"].notna()]
    last = f.index[-1]
    days = pd.date_range(last + pd.Timedelta(days=1), _week_close(last), freq="D")
    add = pd.DataFrame(index=days, columns=f.columns, dtype=float)
    for k in ("open", "high", "low", "close"):
        add[k] = float(C)
    add["funding"] = float(f["funding"].ffill().iloc[-1]) if f["funding"].notna().any() else 0.0
    flow = current_flow(f) if flow is None else flow
    win = pd.date_range(days[-1] - pd.Timedelta(days=W.FLOW_N), days[-1] - pd.Timedelta(days=1), freq="D")
    known = f["pf14z"].reindex(win).dropna()
    na = int(sum(d in days for d in win))
    if na:
        add.loc[add.index.isin(win), "pf14z"] = ((len(known) + na) * flow - float(known.sum())) / na
        add.loc[~add.index.isin(win), "pf14z"] = flow
    out = pd.concat([f, add])
    out.index.name = f.index.name
    return out


def current_flow(f: pd.DataFrame) -> float:
    return float(W.live_flow(f[f["close"].notna()]).dropna().iloc[-1])


def proj_bar(f: pd.DataFrame, C: float, flow: float | None = None) -> pd.Series:
    """Candela settimanale proiettata (ultima riga di weekly_bars) con chiusura C."""
    return W.weekly_bars(project(f, C, flow)).iloc[-1]


def thresholds(w: pd.DataFrame) -> dict:
    """Soglie in forma chiusa sulle settimane chiuse w (weekly_bars dei dati): la prossima candela chiude a C."""
    c = w["close"]
    s39 = float(c.iloc[-(W.SMA - 1):].sum())
    a8, a21, a5 = (2 / (n + 1) for n in W.MACD_P)
    e8 = float(c.ewm(span=W.MACD_P[0], adjust=False).mean().iloc[-1])
    e21m = float(c.ewm(span=W.MACD_P[1], adjust=False).mean().iloc[-1])
    k = (1 - a8) * e8 - (1 - a21) * e21m            # MACD(C) = (a8 − a21)·C + k
    sig = float(w["macd_sig"].iloc[-1])
    return {"sma40": s39 / (W.SMA - 1),                               # C < soglia ⇔ chiusura sotto la SMA40 proiettata
            "sma40_falling": W.SMA * float(w["sma"].iloc[-4]) - s39,  # C < soglia ⇔ SMA40 in calo su 4 settimane
            "ema20": float(w["ema20"].iloc[-1]),                      # C < soglia ⇔ EMA20 in calo
            "ema21": float(w["ema21"].iloc[-1]),                      # C < soglia ⇔ chiusura sotto la EMA21 proiettata
            "macd_cross": (sig - k) / (a8 - a21),                     # C > soglia ⇔ MACD sopra il segnale
            "macd_zero": -k / (a8 - a21),                             # C > soglia ⇔ MACD sopra zero
            "trend_age_prev": int(w["trend_age"].iloc[-1])}


def outcome(f: pd.DataFrame, C: float, side: int, flow: float | None = None) -> str:
    """Esito di W3 (weekly._decide) se la settimana chiude a C: short/long (ingresso), exit, hold, none."""
    d = W._decide(proj_bar(f, C, flow), side)
    if d is None:
        return "hold" if side else "none"
    if d[0] == "exit":
        return "exit"
    return "long" if d[1] > 0 else "short"


def _conds(b: pd.Series, prev: pd.Series, sma4: float) -> dict:
    c = float(b["close"])
    return {"below_sma": c < b["sma"], "sma_falling": b["sma"] < sma4, "ema20_falling": b["ema20"] < prev["ema20"],
            "ema20_rising": b["ema20"] > prev["ema20"], "below_ema21": c < b["ema21"], "above_ema21": c > b["ema21"],
            "above_sma": c > b["sma"], "flow_neg": b["flow"] < 0, "flow_pos": b["flow"] > 0, "f1": bool(b["f1_ok"]),
            "dist_long": bool(b["dist_long"]), "dist_short": bool(b["dist_short"])}


SHORT_TXT = {"below_sma": "chiusura sotto la SMA40", "sma_falling": "SMA40 in calo su 4 settimane",
             "ema20_falling": "EMA20 in calo", "below_ema21": "chiusura sotto la EMA21", "flow_neg": "flusso perp negativo"}
LONG_TXT = {"above_sma": "chiusura sopra la SMA40", "ema20_rising": "EMA20 in salita", "above_ema21": "chiusura sopra la EMA21",
            "flow_pos": "flusso perp positivo", "f1": "filtro F1/MACD dei trend vecchi"}


def _detail(out: str, cd: dict, side: int) -> tuple[str, str]:
    if out in ("short", "long"):
        txt = SHORT_TXT if out == "short" else LONG_TXT
        return (f"Segnale {out}", "Tutte le condizioni: " + ", ".join(txt.values())
                + ". Ingresso all'apertura del lunedì (UTC).")
    if out == "exit":
        why = ("chiusura settimanale oltre la EMA21" if (cd["below_ema21"] if side > 0 else cd["above_ema21"])
               else "distribuzione (funding e flusso perp)")
        return "Uscita", f"Uscita all'apertura del lunedì: {why}."
    if out == "hold":
        return "Posizione mantenuta", "Chiusura dal lato giusto della EMA21 e nessuna distribuzione: resta aperta (vale il trailing giornaliero)."
    miss_s = [v for k, v in SHORT_TXT.items() if not cd[k]]
    miss_l = [v for k, v in LONG_TXT.items() if not cd[k]]
    return "Nessun segnale", f"Short: manca {', '.join(miss_s)}. Long: manca {', '.join(miss_l)}."


def scenarios(f: pd.DataFrame, side: int, flow: float, th: dict) -> list[dict]:
    """Fasce di chiusura in ordine crescente che coprono tutto, con esito e motivo (valutati con weekly_bars)."""
    keys = ("ema21",) if side else ("sma40", "sma40_falling", "ema20", "ema21", "macd_cross", "macd_zero")
    pts = sorted({round(th[k], 2) for k in keys if np.isfinite(th[k]) and th[k] > 0})
    edges = [None] + pts + [None]
    w0 = W.weekly_bars(f[f["close"].notna()])
    bands = []
    for lo, hi in zip(edges[:-1], edges[1:]):
        x = (lo + hi) / 2 if lo is not None and hi is not None else (hi * 0.9 if lo is None and hi is not None
                                                                      else lo * 1.1 if lo is not None else float(f["close"].dropna().iloc[-1]))
        wp = W.weekly_bars(project(f, x, flow))
        out = outcome(f, x, side, flow)
        label, det = _detail(out, _conds(wp.iloc[-1], w0.iloc[-1], float(w0["sma"].iloc[-4])), side)
        if bands and bands[-1]["outcome"] == out and bands[-1]["detail"] == det:
            bands[-1]["hi"] = hi
        else:
            bands.append({"lo": lo, "hi": hi, "outcome": out, "label": label, "detail": det})
    return bands


def _liq_context(report: dict | None) -> dict | None:
    try:
        ctx = json.loads(LIQ_CONTEXT.read_text())
    except Exception:  # noqa: BLE001
        return None
    return {"rows": ctx["rows"], "base": ctx["base"], "regime_rows": ctx["regime_rows"], "imb_now": _liq_imb(report),
            "note": ctx["note"]}


def _history(r: dict, w: pd.DataFrame, f: pd.DataFrame, side: str) -> dict:
    trades = [t for t in r["trades"] + ([r["open"]] if r["open"] else []) if t["side"] == side]
    out = []
    for t in trades:
        sig = pd.Timestamp(t["signal"])
        hi8 = float(w.loc[:sig, "high"].iloc[-8:].max())
        seg = f.loc[t["entry"]: t.get("exit") or f.index[-1]]
        px = float(t["entry_px"])
        adv = (float(seg["high"].max()) / px - 1) if side == "short" else (1 - float(seg["low"].min()) / px)
        out.append({"entry": t["entry"], "px": round(px, 2), "drop_from_8w_high_pct": round((px / hi8 - 1) * 100, 1),
                    "move_pct": round(float(t["move"]) * 100, 1), "adverse_pct": round(float(adv) * 100, 1),
                    "reason": W.REASONS.get(t.get("reason", "open"), t.get("reason", "open"))})
    return {"side": side, "trades": out, "wins": sum(1 for t in trades if t["pnl"] > 0), "n": len(trades)}


def _if_signal(sd: str, price: float, bar: pd.Series) -> dict:
    sg = 1 if sd == "long" else -1
    cap = W.CAPITAL * W.SHARE
    p = W.plan(sg, price, float(bar["atr"]), float(bar["ema21"]), cap)
    exits = [f"stop iniziale {_usd(p['stop'])} (2,5 ATR settimanali)",
             f"trailing 2,5 ATR settimanali ({_usd(p['trail_dist'])}) dalla miglior chiusura giornaliera, a cricchetto",
             f"chiusura settimanale {'sotto' if sg > 0 else 'sopra'} la EMA21",
             "distribuzione: " + ("funding medio 7g > 0,0009 e flusso perp < 0" if sg > 0
                                  else "funding medio 7g < −0,0003 e flusso perp > 0")]
    return {"side": sd, "close_est": round(price, 2), "stop": p["stop"], "stop_pct": p["stop_pct"], "expo": p["expo"],
            "loss_at_stop_pct": round(p["loss_usd"] / cap * 100, 2) if cap else 0.0, "capital_usd": round(cap, 0),
            "loss_at_stop_usd": p["loss_usd"], "exits": exits}


def _fmt_day(d: pd.Timestamp) -> str:
    return d.strftime("%d/%m")


# ---------------------------------------------------------------- posizione aperta e quadro di oggi
def _num(x, d: int = 2):
    """Numero finito arrotondato oppure None (dati mancanti: mai NaN nel JSON)."""
    try:
        v = float(x)
    except (TypeError, ValueError):
        return None
    return round(v, d) if np.isfinite(v) else None


def _it(x: float, d: int = 2, sign: bool = True) -> str:
    return (f"{x:+.{d}f}" if sign else f"{x:.{d}f}").replace(".", ",").replace("-", "−")


def _dist_rule(sg: int, fund7: float | None, flow: float | None) -> str:
    """Condizione di distribuzione di W3 per il lato e il suo stato attuale (alla chiusura della domenica)."""
    if sg > 0:
        rule, on = "funding medio 7g > 0,0009 e flusso perp < 0", (fund7 is not None and flow is not None
                                                                 and fund7 > W.FUND_HOT and flow < 0)
    else:
        rule, on = "funding medio 7g < −0,0003 e flusso perp > 0", (fund7 is not None and flow is not None
                                                                  and fund7 < W.FUND_COLD and flow > 0)
    now = ("proiezione a domenica " + (f"funding 7g {fund7:.5f}".replace(".", ",").replace("-", "−") if fund7 is not None else "funding n.d.")
           + (f", flusso {_sig(flow)}" if flow is not None else ", flusso n.d."))
    return (f"{'Long' if sg > 0 else 'Short'}: esce alla chiusura della domenica se {rule}. Ora, {now}: "
            + ("ATTIVA (uscita se resta così alla chiusura)." if on else "non attiva."))


def position_block(o: dict | None, pend: dict | None, w: pd.DataFrame, th: dict, price: float, last: pd.Timestamp,
                   bar: pd.Series, flow: float | None) -> dict | None:
    """Posizione W3 per la sezione Oggi: None se flat (o se l'uscita è già decisa per l'apertura di lunedì).
    PnL sul capitale CAPITAL·SHARE con l'esposizione del trade (motore di simulate: commissioni e funding inclusi)."""
    cap = W.CAPITAL * W.SHARE
    if pend and pend["kind"] == "exit":
        return None
    fund7 = _num(bar.get("fund7"), 6)
    if o:
        sg = 1 if o["side"] == "long" else -1
        stop, pnl = float(o["trail"]), float(o["pnl"])
        entry = pd.Timestamp(o["entry"])
        return {"side": o["side"], "entry_date": str(o["entry"]), "entry_px": _num(o["entry_px"]), "price": _num(price),
                "pnl_pct": _num(pnl * 100), "pnl_usd": _num(cap * pnl, 0), "capital_usd": _num(cap, 0),
                "stop": _num(stop), "stop_dist_pct": _num((stop / price - 1) * 100),
                "trail_best": _num(o["best"]), "exit_ema21_threshold": _num(th["ema21"]),
                "dist_rule": _dist_rule(sg, fund7, flow), "days_open": int((last - entry).days) + 1}
    if pend and pend["kind"] == "enter":   # segnale di domenica: ingresso all'apertura di lunedì, prezzo non ancora noto
        sg = int(pend["arg"])
        wk = w.iloc[-1]
        stop = float(wk["close"]) - sg * W.STOP_K * float(wk["atr"])
        return {"side": "long" if sg > 0 else "short", "entry_date": str((pd.Timestamp(pend["date"]) + pd.Timedelta(days=1)).date()),
                "entry_px": None, "price": _num(price), "pnl_pct": None, "pnl_usd": None, "capital_usd": _num(cap, 0),
                "stop": _num(stop), "stop_dist_pct": _num((stop / price - 1) * 100), "trail_best": None,
                "exit_ema21_threshold": _num(th["ema21"]), "dist_rule": _dist_rule(sg, fund7, flow), "days_open": 0}
    return None


def _table(path: Path) -> dict | None:
    try:
        return json.loads(path.read_text())
    except Exception:  # noqa: BLE001
        return None


def _terz(x: float | None, th: float = 0.43) -> str | None:
    if x is None:
        return None
    return "lo" if x < -th else "hi" if x > th else "mid"


TERZ_TXT = {"lo": "basso", "mid": "medio", "hi": "alto"}
FLOW_TXT = {"lo": "in vendita", "mid": "quasi neutro", "hi": "in acquisto"}


def analog(pf: float | None, sf: float | None, tab: dict | None = None) -> dict | None:
    """Cella storica N4 più vicina allo stato attuale (pf14z e sf14z a terzili fissi ±0,43); ripiego sul terzile singolo."""
    tab = tab if tab is not None else _table(ANALOG)
    if not tab:
        return None
    th = float((tab.get("thresholds") or {}).get("hi", 0.43))
    tp, ts = _terz(pf, th), _terz(sf, th)
    cells = tab.get("cells") or {}
    keys = ([f"PFt={tp} & SFt={ts}"] if tp and ts else []) + ([f"PFt={tp}"] if tp else []) + ([f"SFt={ts}"] if ts else [])
    key = next((k for k in keys if k in cells), None)
    if key is None:
        return None
    c, b = cells[key], tab.get("base") or {}
    parts = ([f"pf14z {TERZ_TXT[tp]}"] if "PFt" in key else []) + ([f"sf14z {TERZ_TXT[ts]}"] if "SFt" in key else [])
    base = (f" (base {_it(b['p7'], 0, False)}% a 7 g, {_it(b['p30'], 0, False)}% a 30 g)" if "p7" in b and "p30" in b else "")
    return {"label": " · ".join(parts) + f", dal 2021" + base, "n": int(c["n_ind7"]),
            "p7": c["p7"], "ci7": list(c["ci7"]), "p30": c["p30"], "ci30": list(c["ci30"]), "mean7": c["mean7"]}


def _bucket(d: float) -> str | None:
    return "0-3%" if d < 0.03 else "3-8%" if d < 0.08 else "8-15%" if d < 0.15 else None


def sr_rows(levels: dict | None, tab: dict | None = None, min_touches: int = 20) -> list[dict]:
    """Livelli del report con la tenuta storica D3 (N4) per lato, tipo e distanza; tipo con < min_touches tocchi → tutti i tipi.
    Oltre il 15% di distanza: fuori dal test (None)."""
    if not levels:
        return []
    tab = tab if tab is not None else _table(SR_HOLD)
    rows = {(r["side"], r["type"], r["dist"]): r for r in (tab or {}).get("rows", []) if r.get("scale") == "D3"}
    out = []
    for key, tag in (("resistances", "R"), ("supports", "S")):
        for i, z in enumerate(levels.get(key) or []):
            try:
                d = float(z["dist_pct"]) / 100
                side = "resistenza" if key == "resistances" else "supporto"
                typ = "W" if z.get("weekly") else ("V" if not z.get("touches") else "G")
                b = _bucket(abs(d))
                r = rows.get((side, typ, b)) if b else None
                if b and (r is None or r["touches"] < min_touches):
                    r = rows.get((side, "tutti", b))
                out.append({"name": f"{tag}{i + 1}", "lo": _num(z["lo"], 0), "hi": _num(z["hi"], 0), "dist_pct": _num(d * 100),
                            "hold_pct": r["hold_pct"] if r else None, "random_pct": r["random_pct"] if r else None})
            except Exception:  # noqa: BLE001
                continue
    return sorted(out, key=lambda x: -(x["dist_pct"] if x["dist_pct"] is not None else 0))


def _last(f: pd.DataFrame, k: str) -> float | None:
    if k not in f:
        return None
    s = f[k].dropna()
    return _num(s.iloc[-1], 6) if len(s) else None


def _liq_imb(report: dict | None) -> float | None:
    lm = (report or {}).get("liqmap") or {}
    try:
        p, bins = float(lm["price"]), lm["bins"]
        s = sum(b[2] for b in bins if p < b[0] <= p * 1.08)
        lo = sum(b[1] for b in bins if p * 0.92 <= b[0] < p)
        return round((s - lo) / (s + lo), 3) if s + lo > 0 else None
    except Exception:  # noqa: BLE001
        return None


def _liq24(report: dict | None) -> dict | None:
    """Liquidazioni reali 24h (radar/liqsources). Se il giro non le ha ancora calcolate le legge dai file locali (niente rete)."""
    rep = report or {}
    ls = rep.get("liqsources")
    if ls is None and "liqsources" not in rep:
        try:
            from . import liqsources
            ls = liqsources.summary()
        except Exception:  # noqa: BLE001
            ls = None
    try:
        t = ls["total"]["24h"]
        return {"long": float(t["long_usd"]), "short": float(t["short_usd"]), "stale": bool(ls.get("stale"))}
    except Exception:  # noqa: BLE001
        return None


def _musd(x: float) -> str:
    return f"{x / 1e6:,.1f} M$".replace(",", "X").replace(".", ",").replace("X", ".")


def today(f: pd.DataFrame, w: pd.DataFrame, report: dict | None, price: float, side: int = 0) -> dict:
    """Quadro di oggi: ogni voce con lettura breve e affidabilità dagli studi. Mai eccezioni: le voci senza dati si saltano."""
    items: list[dict] = []
    tab = _table(ANALOG) or {}
    cells = tab.get("cells") or {}
    base30 = (tab.get("base") or {}).get("p30")

    def add(key, label, value, read, rel):
        items.append({"key": key, "label": label, "value": value, "read": read, "reliability": rel})

    def single(k: str) -> str:
        c = cells.get(k)
        return (f"; storicamente {_it(c['p30'], 0, False)}% di rialzo a 30 g (base {_it(base30, 0, False)}%)"
                if c and base30 is not None else "")
    pf, sf = _last(f, "pf14z"), _last(f, "sf14z")
    try:
        if pf is not None:
            t = _terz(pf)
            add("pf14z", "Flusso perp (pf14z)", _sig(pf),
                f"terzile {TERZ_TXT[t]}: perp {FLOW_TXT[t]}" + single(f"PFt={t}"),
                "W3 ne usa il segno (media di 3 giorni) per gli ingressi; come probabilità a 7–30 g nessun vantaggio "
                "dopo la correzione (lezione 97)")
        if sf is not None:
            t = _terz(sf)
            add("sf14z", "Flusso spot (sf14z)", _sig(sf),
                f"terzile {TERZ_TXT[t]}: spot {FLOW_TXT[t]}" + single(f"SFt={t}"),
                "contesto: nessun vantaggio dimostrato (lezione 97)")
        if pf is not None and sf is not None:
            dv = sf - pf
            rd = ("guida lo spot (spot compra più del perp)" if dv > 0.5 else "guida il perp (perp compra più dello spot)"
                  if dv < -0.5 else "spot e perp allineati")
            add("div", "Divergenza spot − perp", _sig(dv), rd,
                "tesi perp in vendita/spot che assorbe: +1/+3 punti a 7 g ma non regge al placebo (lezione 89)")
        fund7 = _num(f["funding"].fillna(0).rolling(7).mean().iloc[-1], 6) if "funding" in f and f["funding"].notna().any() else None
        if fund7 is not None:
            fz = _last(f, "funding_z")
            rd = ("funding " + ("alto" if (fz or 0) > 0.43 else "basso" if (fz or 0) < -0.43 else "nella media")
                  + (f" (z {_it(fz)})" if fz is not None else ""))
            if side:
                rd += "; distribuzione " + ("attiva" if (fund7 > W.FUND_HOT if side > 0 else fund7 < W.FUND_COLD)
                                            else "lontana") + f" (soglia {'> 0,0009' if side > 0 else '< −0,0003'})"
            add("funding", "Funding (media 7g)", f"{fund7 * 100:.4f}%/giorno · {fund7 * 365 * 100:.1f}%/anno".replace(".", ",")
                .replace("-", "−"), rd, "contesto (lezione 97); in W3 conta solo dentro la condizione di distribuzione")
        oi7 = _last(f, "oi_chg7")
        if oi7 is not None:
            oz = _last(f, "oi_z")
            rd = ("OI " + ("in aumento" if oi7 > 0 else "in calo") + (f" (z {_it(oz)})" if oz is not None else ""))
            if pf is not None and pf < 0 and oz is not None and oz > 0.43:
                rd += "; perp in vendita con OI in aumento: nuovi short aperti (36% di rialzo a 7 g, non significativo)"
            add("oi7", "Open interest, variazione 7g", f"{oi7 * 100:+.1f}%".replace(".", ",").replace("-", "−"), rd,
                "contesto: 0 celle su 5.790 superano la correzione (lezione 97)")
        lq = _liq24(report)
        if lq is not None:
            cas = (report or {}).get("cascade") or {}
            rd = ("più long liquidati" if lq["long"] > 1.5 * lq["short"] else "più short liquidati"
                  if lq["short"] > 1.5 * lq["long"] else "equilibrate")
            if cas.get("active"):
                rd += f"; cascata {cas.get('side', '')} {cas.get('start_utc', '')}→{cas.get('end_utc', '')} ({_it(float(cas.get('move_pct') or 0), 1)}%)"
            if lq["stale"]:
                rd += "; fonti ferme da oltre 6 ore"
            add("liq24h", "Liquidazioni 24h (exchange registrati)", f"long {_musd(lq['long'])} · short {_musd(lq['short'])}", rd,
                "dicono quanta leva è stata pulita, non dove va il prezzo; dopo una cascata nessun vantaggio a comprare "
                "(lezioni 72, 90, 92)")
        imb = _liq_imb(report)
        if imb is not None:
            rd = ("bilanciata" if abs(imb) < 0.15 else "più short da liquidare sopra" if imb > 0 else "più long da liquidare sotto")
            add("liqmap_imb", "Squilibrio mappa liquidazioni ±8% (stima)", f"{imb * 100:+.0f}%".replace("-", "−"), rd,
                "stima; non attira il prezzo e non rafforza gli S/R, vale al più 12–24 ore (lezioni 81, 93)")
        wk = w.iloc[-1]
        for key, col, lab in (("dist_sma40", "sma", "SMA40"), ("dist_ema21", "ema21", "EMA21")):
            m = _num(wk.get(col))
            if m:
                d = (price / m - 1) * 100
                rd = f"{'sotto' if d < 0 else 'sopra'} la {lab} settimanale ({_usd(m)}, ultima chiusura)"
                rel = ("W3 usa il lato della SMA40 come regime; la distanza come probabilità non dà vantaggio (lezione 97)"
                       if col == "sma" else "W3 esce/entra sul lato della EMA21 alla chiusura; la distanza da sola non dà "
                       "vantaggio (lezione 97)")
                add(key, f"Distanza dalla {lab} settimanale", f"{d:+.1f}%".replace(".", ",").replace("-", "−"), rd, rel)
    except Exception as e:  # noqa: BLE001
        print(f"[preview] quadro di oggi incompleto: {e!r}")
    try:
        sr = sr_rows((report or {}).get("levels"))
    except Exception:  # noqa: BLE001
        sr = []
    try:
        an = analog(pf, sf, tab or None)
    except Exception:  # noqa: BLE001
        an = None
    return {"updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"), "items": items, "sr": sr, "analog": an,
            "note": TODAY_NOTE}


def build(f: pd.DataFrame | None, report: dict | None = None) -> dict | None:
    """Pre-analisi della prossima decisione W3; None se i dati non bastano."""
    if f is None or not isinstance(f, pd.DataFrame) or f.empty or any(k not in f for k in NEED):
        return None
    f = f[f["close"].notna()]
    try:
        w = W.weekly_bars(f)
        if len(w) < W.SMA + 5 or w[["sma", "ema21", "ema20", "atr"]].iloc[-5:].isna().any().any():
            return None
        flow = current_flow(f)
        r = W.simulate(f)
    except Exception as e:  # noqa: BLE001
        print(f"[preview] dati insufficienti: {e!r}")
        return None
    last, price = f.index[-1], float(f["close"].iloc[-1])
    sun = _week_close(last)
    o, pend = r["open"], r["pending"]
    side = (1 if o["side"] == "long" else -1) if o else 0
    if pend:   # decisione già presa (dati fino a domenica): vale la posizione dopo l'esecuzione di lunedì
        side = pend["arg"] if pend["kind"] == "enter" else 0
    th = thresholds(w)
    bar = proj_bar(f, price, flow)
    sma4 = float(w["sma"].iloc[-4])
    cd = _conds(bar, w.iloc[-1], sma4)
    sc = scenarios(f, side, flow, th)

    def thr(k):
        return _usd(th[k])
    conditions = []
    if not side:
        age = int(bar["trend_age"])
        conditions = [
            {"key": "below_sma40", "label": "Chiusura sotto la SMA40 (proiettata)", "now": bool(cd["below_sma"]),
             "value": f"SMA40 a fine settimana {_usd(bar['sma'])}; sotto se chiude < {thr('sma40')}", "depends_on_close": True},
            {"key": "sma40_falling", "label": "SMA40 in calo su 4 settimane", "now": bool(cd["sma_falling"]),
             "value": f"contro {_usd(sma4)} di 4 settimane prima; in calo se chiude < {thr('sma40_falling')}", "depends_on_close": True},
            {"key": "ema20_falling", "label": "EMA20 settimanale in calo", "now": bool(cd["ema20_falling"]),
             "value": f"in calo se chiude < {thr('ema20')}, in salita sopra", "depends_on_close": True},
            {"key": "below_ema21", "label": "Chiusura sotto la EMA21 (proiettata)", "now": bool(cd["below_ema21"]),
             "value": f"EMA21 a fine settimana {_usd(bar['ema21'])}; sotto se chiude < {thr('ema21')}", "depends_on_close": True},
            {"key": "flow_neg", "label": "Flusso perp negativo (short) / positivo (long)", "now": bool(cd["flow_neg"]),
             "value": _sig(flow), "depends_on_close": False},
            {"key": "above_sma40", "label": "Long: chiusura sopra la SMA40 (proiettata)", "now": bool(cd["above_sma"]),
             "value": f"sopra se chiude > {thr('sma40')}", "depends_on_close": True},
            {"key": "ema20_rising", "label": "Long: EMA20 settimanale in salita", "now": bool(cd["ema20_rising"]),
             "value": f"in salita se chiude > {thr('ema20')}", "depends_on_close": True},
            {"key": "f1_macd", "label": "Long: filtro F1/MACD (trend vecchi)", "now": bool(cd["f1"]),
             "value": f"MACD sopra il segnale se chiude > {thr('macd_cross')}, sopra zero > {thr('macd_zero')}; "
                      f"serve solo da {W.OLD_TREND} settimane sopra la SMA40", "depends_on_close": True},
            {"key": "trend_age", "label": f"Trend vecchio (≥ {W.OLD_TREND} settimane sopra la SMA40)", "now": age >= W.OLD_TREND,
             "value": f"{age} settimane a questa chiusura (finora {th['trend_age_prev']}); si azzera sotto {thr('sma40')}",
             "depends_on_close": True}]
    else:
        L = side > 0
        dist = bool(cd["dist_long"] if L else cd["dist_short"])
        conditions = [
            {"key": "exit_ema21", "label": f"Uscita: chiusura {'sotto' if L else 'sopra'} la EMA21 (proiettata)",
             "now": bool(cd["below_ema21"] if L else cd["above_ema21"]),
             "value": f"uscita se chiude {'<' if L else '>'} {thr('ema21')}", "depends_on_close": True},
            {"key": "dist", "label": "Uscita: distribuzione (funding 7g e flusso perp)", "now": dist,
             "value": f"funding 7g {float(bar['fund7']):.5f}".replace(".", ",") + f" · flusso {_sig(flow)}",
             "depends_on_close": False}]
        if o:
            conditions.append({"key": "trail", "label": "Trailing / stop attuale (controllo giornaliero)", "now": None,
                               "value": f"stop {_usd(o['trail'])} (iniziale {_usd(o['stop0'])}, miglior chiusura {_usd(float(o['best']))})",
                               "depends_on_close": False})
    # lato del segnale più vicino al prezzo attuale
    sig_b = [b for b in sc if b["outcome"] in ("short", "long")]

    def dist_to(b):
        lo, hi = b["lo"] if b["lo"] is not None else -np.inf, b["hi"] if b["hi"] is not None else np.inf
        return 0.0 if lo <= price <= hi else min(abs(price - lo), abs(price - hi))
    near = min(sig_b, key=dist_to) if sig_b else None
    sd = near["outcome"] if near else ("long" if side > 0 else "short" if side < 0 else None)
    try:
        pos_block = position_block(o, pend, w, th, price, last, bar, flow)
    except Exception as e:  # noqa: BLE001
        print(f"[preview] posizione non calcolata: {e!r}")
        pos_block = None
    today_d = today(f, w, report, price, side)
    win = [last - pd.Timedelta(days=k) for k in (W.FLOW_N, 1)]
    fwin = [sun - pd.Timedelta(days=k) for k in (W.FLOW_N, 1)]
    need = None if not near else ("neg" if near["outcome"] == "short" else "pos")
    flow_d = {"value": round(flow, 3), "sign_needed": need,
              "note": f"Flusso attuale (media pf14z {_fmt_day(win[0])}–{_fmt_day(win[1])}); alla chiusura di domenica "
                      f"userà {_fmt_day(fwin[0])}–{_fmt_day(fwin[1])}."}
    return {"decision_utc": f"{(sun + pd.Timedelta(days=1)).date()} 00:00", "week_close_utc": str(sun.date()),
            "price": round(price, 2), "position": "long" if side > 0 else "short" if side < 0 else "flat",
            "conditions": conditions, "scenarios": sc, "flow": flow_d,
            "if_signal": _if_signal(near["outcome"], price, bar) if near else None,
            "history": _history(r, w, f, sd) if sd else None,
            "liq_context": _liq_context(report), "note": NOTE,
            "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M"),
            "position_block": pos_block, "today": today_d}
