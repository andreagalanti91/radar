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
"""
from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path

import numpy as np
import pandas as pd

from . import weekly as W

LIQ_CONTEXT = Path(__file__).resolve().parent.parent / "research" / "preview" / "liq_context.json"
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
    imb = None
    lm = (report or {}).get("liqmap") or {}
    try:
        p, bins = float(lm["price"]), lm["bins"]
        s = sum(b[2] for b in bins if p < b[0] <= p * 1.08)
        lo = sum(b[1] for b in bins if p * 0.92 <= b[0] < p)
        imb = round((s - lo) / (s + lo), 3) if s + lo > 0 else None
    except Exception:  # noqa: BLE001
        imb = None
    return {"rows": ctx["rows"], "base": ctx["base"], "regime_rows": ctx["regime_rows"], "imb_now": imb, "note": ctx["note"]}


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
            "updated_utc": datetime.now(timezone.utc).strftime("%Y-%m-%d %H:%M")}
