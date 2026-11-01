"""Segnale SETTIMANALE W2 (attivato il 31/10/2026, decisione dell'utente): poche operazioni, grandi movimenti.

Regole (candele settimanali W-SUN chiuse, decisione alla chiusura UTC della domenica, esecuzione all'apertura del lunedì):
- regime long  = chiusura sopra la SMA 40 settimane ed EMA 20 settimanale in salita
- regime short = chiusura sotto la SMA 40, SMA 40 in calo su 4 settimane ed EMA 20 in calo
- ingresso: chiusura dal lato giusto della EMA 21 settimanale e flusso perp pf14z > 0 (long) / < 0 (short)
- filtro F1 (dal 01/11/2026, decisione dell'utente "teniamo le due strategie migliori"): nei trend vecchi
  (chiusura sopra la SMA 40 da almeno 16 settimane) un nuovo long entra solo se MACD settimanale (8,21,5) è sopra
  la linea di segnale e sopra zero (ricerca AP12A, lezione 64)
- uscita alla prima: trailing 2,5 ATR settimanali dalla miglior chiusura giornaliera (controllo giornaliero);
  chiusura settimanale oltre la EMA 21; distribuzione (long: funding medio 7g > 0,0009/giorno e pf14z < 0;
  short: funding < −0,0003 e pf14z > 0). Stop iniziale 2,5 ATR settimanali dalla chiusura del segnale.
- esecuzione: long in SPOT a 1x (commissione 0,1%/lato, niente funding); short in PERP con esposizione
  min(1, 0,25 / (2,5·ATRw/close)) = tetto di rischio del 25% allo stop (commissione 0,05%/lato, funding reale).
  Slippage 0,1%. Il tetto sugli short è stato scelto dopo i risultati (ricerca W5), per prudenza.
Motore di riferimento della ricerca: /tmp/radar-work/w5/scripts/sim3.py (W2 V1, R=0,25, solo short), riscritto qui
senza le varianti non usate. Stato dal vivo in data/state.json (chiave "weekly"), eventi Telegram con dedupe.
Importi su RADAR_CAPITAL × RADAR_WEEKLY_SHARE (quota del capitale dedicata al settimanale: la sceglie l'utente).
"""
from __future__ import annotations

import os
from datetime import datetime, timezone

import numpy as np
import pandas as pd

START = "2021-01-01"
LIVE_START = "2026-10-31"
SMA, EMA_T, EMA_X, ATR_N = 40, 20, 21, 14
STOP_K = TRAIL_K = 2.5
FUND_HOT, FUND_COLD = 0.0009, -0.0003
R_SHORT = 0.25                     # rischio massimo allo stop iniziale per gli short (frazione del capitale)
OLD_TREND, MACD_P = 16, (8, 21, 5)  # filtro F1 (01/11/2026): nei trend vecchi nuovo long solo con momentum MACD ripartito
FEE_SPOT, FEE_PERP, SLIP = 0.001, 0.0005, 0.001
CAPITAL = float(os.environ.get("RADAR_CAPITAL", "50000"))
SHARE = float(os.environ.get("RADAR_WEEKLY_SHARE", "1.0"))   # quota di RADAR_CAPITAL dedicata al settimanale
REASONS = {"trail": "trailing 2,5 ATR settimanali", "stop": "stop iniziale 2,5 ATR settimanali",
           "ema": "chiusura settimanale oltre la EMA 21", "dist": "distribuzione (funding e flusso perp)",
           "open": "posizione aperta"}


def weekly_bars(f: pd.DataFrame) -> pd.DataFrame:
    """Candele settimanali W-SUN CHIUSE (solo settimane complete nei dati) con medie, ATR, flusso e funding."""
    w = f[["open", "high", "low", "close"]].resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    w["flow"] = f["pf14z"].resample("W-SUN").last()
    w["fund7"] = f["funding"].fillna(0).rolling(7).mean().resample("W-SUN").last()
    c = w["close"]
    w["sma"] = c.rolling(SMA).mean()
    w["ema20"] = c.ewm(span=EMA_T, adjust=False).mean()
    w["ema21"] = c.ewm(span=EMA_X, adjust=False).mean()
    tr = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
    w["atr"] = tr.ewm(alpha=1 / ATR_N, adjust=False).mean()
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    above = (c > w["sma"]).astype(int)
    w["trend_age"] = above.groupby((above == 0).cumsum()).cumsum()          # settimane consecutive sopra la SMA 40
    m = c.ewm(span=MACD_P[0], adjust=False).mean() - c.ewm(span=MACD_P[1], adjust=False).mean()
    w["macd"], w["macd_sig"] = m, m.ewm(span=MACD_P[2], adjust=False).mean()
    w["f1_ok"] = (w["trend_age"] < OLD_TREND) | ((w["macd"] > w["macd_sig"]) & (w["macd"] > 0))
    w["long"] = (up & (c > w["ema21"]) & (w["flow"] > 0) & w["f1_ok"]).fillna(False)
    w["short"] = (dn & (c < w["ema21"]) & (w["flow"] < 0)).fillna(False)
    w["dist_long"] = ((w["fund7"] > FUND_HOT) & (w["flow"] < 0)).fillna(False)
    w["dist_short"] = ((w["fund7"] < FUND_COLD) & (w["flow"] > 0)).fillna(False)
    return w[w.index <= f.index[-1]]


def exposure(sg: int, close: float, atr: float, lev: float = 1.0) -> float:
    """Esposizione sul capitale: long 1x; short con tetto di rischio 25% allo stop iniziale (2,5 ATRw)."""
    if sg > 0:
        return lev
    return lev * min(1.0, R_SHORT / (STOP_K * atr / close))


def _decide(wk: pd.Series, side: int) -> tuple | None:
    """Decisione alla chiusura della domenica: uscita (in posizione) o ingresso (flat), eseguiti all'apertura del lunedì."""
    if side:
        beyond = wk["close"] < wk["ema21"] if side > 0 else wk["close"] > wk["ema21"]
        if beyond:
            return ("exit", "ema")
        if wk["dist_long"] if side > 0 else wk["dist_short"]:
            return ("exit", "dist")
        return None
    if wk["long"]:
        return ("enter", 1)
    if wk["short"]:
        return ("enter", -1)
    return None


def simulate(f: pd.DataFrame, start: str = START, capital: float = 10000.0, lev: float = 1.0) -> dict:
    """Storico W2 sui dati giornalieri: trade chiusi, equity giornaliera, posizione aperta e decisione in sospeso
    (presa sull'ultima domenica dei dati, da eseguire alla prossima apertura). lev=2: esposizione raddoppiata,
    long 2x metà spot e metà perp (come nella ricerca)."""
    f = f[f["close"].notna()]
    w = weekly_bars(f)
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)

    def close_all(px: float, i: int, reason: str) -> None:
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1,
                  move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = exposure(side, wk["close"], wk["atr"], lev)
                fs = min(lt, 1.0) / lt if side > 0 else 0.0   # quota spot: long fino a 1x in spot, il resto in perp
                frate, fperp = fs * FEE_SPOT + (1 - fs) * FEE_PERP, 1 - fs
                px = O[i] * (1 + SLIP * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=round(px, 2), sig_close=float(wk["close"]), atr=float(wk["atr"]), expo=round(lt, 3),
                          market="spot" if side > 0 and lev <= 1 else "perp", eq0=cash + abs(q) * px * frate,
                          stop0=float(wk["close"] - side * STOP_K * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
            pend = None
        if side:
            tl = tr["best"] - side * TRAIL_K * tr["curatr"]
            stop = max(tr["stop0"], tl) if side > 0 else min(tr["stop0"], tl)
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = _decide(wk, side)
            pend = d + (wk, day) if d else None
    out = {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "weekly": w, "open": None, "pending": None}
    if side:
        i = len(idx) - 1
        tl = tr["best"] - side * TRAIL_K * tr["curatr"]
        trail = max(tr["stop0"], tl) if side > 0 else min(tr["stop0"], tl)   # livello valido dal prossimo giorno
        out["open"] = dict(tr, trail=float(trail), last=float(C[i]), move=(C[i] / tr["entry_px"] - 1) * side,
                           pnl=(eq[i] / tr["eq0"] - 1),
                           # come nella ricerca: per le metriche la posizione aperta si chiude all'ultima chiusura (con commissione)
                           pnl_close=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1)
    if pend is not None:
        out["pending"] = {"kind": pend[0], "arg": pend[1], "date": str(pend[3].date())}
    return out


def metrics(r: dict) -> dict:
    """Numeri della ricerca: trade/anno, WR, medio, peggiore, rendimento, DD giornaliero, MAR, anni.
    La posizione aperta conta come chiusa all'ultima chiusura giornaliera (come nella ricerca)."""
    trades = r["trades"] + ([dict(r["open"], pnl=r["open"]["pnl_close"])] if r["open"] else [])
    e = r["equity"] / r["equity"].iloc[0]
    pn = np.array([t["pnl"] for t in trades]) if trades else np.zeros(0)
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    tot, dd = float(e.iloc[-1] - 1), float((e / e.cummax() - 1).min())
    ye = pd.concat([pd.Series([1.0]), e.resample("YE").last().reset_index(drop=True)]).pct_change().dropna()
    return {"n": len(trades), "per_year": round(len(trades) / yrs, 2),
            "win_rate": round(float((pn > 0).mean() * 100), 1) if len(pn) else None,
            "avg_pct": round(float(pn.mean() * 100), 2) if len(pn) else None,
            "worst_pct": round(float(pn.min() * 100), 2) if len(pn) else None,
            "best_pct": round(float(pn.max() * 100), 2) if len(pn) else None,
            "total_pct": round(tot * 100, 1), "max_dd_pct": round(dd * 100, 1),
            "mar": round(tot / abs(dd), 2) if dd < 0 else None,
            "years": {str(y.year): round(float(v * 100), 1) for y, v in zip(e.resample("YE").last().index, ye)}}


def _dash(t: dict) -> dict:
    return {"signal": t["signal"], "entry": t["entry"], "side": t["side"], "market": t["market"], "expo": t["expo"],
            "entry_px": t["entry_px"], "exit": t.get("exit"), "exit_px": t.get("exit_px"), "reason": t.get("reason", "open"),
            "move_pct": round(t["move"] * 100, 2), "pnl_pct": round(t["pnl"] * 100, 2)}


def plan(side: int, close: float, atr: float, ema21: float, capital: float) -> dict:
    """Piano in dollari per un ingresso: mercato, esposizione, quantità, stop iniziale, perdita allo stop."""
    ex = exposure(side, close, atr)
    stop = close - side * STOP_K * atr
    stop_pct = STOP_K * atr / close
    notional = capital * ex
    return {"market": "spot" if side > 0 else "perp", "expo": round(ex, 3), "capital": round(capital, 0),
            "notional": round(notional, 0), "btc": round(notional / close, 4), "entry_est": round(close, 2),
            "stop": round(stop, 2), "stop_pct": round(stop_pct * 100, 2),
            "loss_usd": round(notional * (stop_pct + SLIP + 2 * (FEE_SPOT if side > 0 else FEE_PERP)), 0),
            "trail_dist": round(TRAIL_K * atr, 2), "ema21": round(ema21, 2)}


def evaluate(f: pd.DataFrame, capital: float | None = None) -> dict:
    """Stato attuale W2: nessuno / segnale (ingresso alla prossima apertura) / aperto / uscita (alla prossima apertura),
    con livelli e piano in dollari, più lo storico dal 2021 a 1x e 2x."""
    capital = CAPITAL * SHARE if capital is None else capital
    f = f[f["close"].notna()]
    r = simulate(f)
    r2 = simulate(f, lev=2.0)
    w = r["weekly"]
    wk, last = w.iloc[-1], f.iloc[-1]
    o, pd_ = r["open"], r["pending"]
    fund7 = float(f["funding"].fillna(0).rolling(7).mean().iloc[-1])
    flow = float(f["pf14z"].dropna().iloc[-1])
    out = {"date": str(f.index[-1].date()), "week": str(w.index[-1].date()), "price": float(last["close"]),
           "atr_d": float(last["atr"]) if "atr" in f else None, "atr_w": float(wk["atr"]), "ema21": float(wk["ema21"]),
           "sma40": float(wk["sma"]), "ema20": float(wk["ema20"]), "flow": flow, "fund7": fund7,
           "regime": "long" if wk["close"] > wk["sma"] and wk["ema20"] > w["ema20"].iloc[-2] else
                     "short" if wk["close"] < wk["sma"] and wk["sma"] < w["sma"].iloc[-5] and wk["ema20"] < w["ema20"].iloc[-2]
                     else "neutro",
           "capital": round(capital, 0), "share": SHARE, "status": "nessuno"}
    if o:
        sg = 1 if o["side"] == "long" else -1
        out.update(status="aperto", side=o["side"], signal_date=o["signal"], entry=o["entry"], entry_px=o["entry_px"],
                   market=o["market"], expo=o["expo"], stop0=round(o["stop0"], 2), trail=round(o["trail"], 2),
                   best=round(float(o["best"]), 2), move_pct=round(o["move"] * 100, 2), pnl_pct=round(o["pnl"] * 100, 2),
                   notional=round(capital * o["expo"], 0), btc=round(capital * o["expo"] / o["entry_px"], 4),
                   dist_now=bool((fund7 > FUND_HOT and flow < 0) if sg > 0 else (fund7 < FUND_COLD and flow > 0)),
                   trail_usd=round(capital * o["expo"] * (o["trail"] / o["entry_px"] - 1) * sg, 0))
        if pd_ and pd_["kind"] == "exit":
            out.update(status="uscita", reason=pd_["arg"], exit_date=pd_["date"])
    elif pd_ and pd_["kind"] == "enter":
        sg = pd_["arg"]
        out.update(status="segnale", side="long" if sg > 0 else "short", signal_date=pd_["date"],
                   plan=plan(sg, float(wk["close"]), float(wk["atr"]), float(wk["ema21"]), capital))
    m1, m2 = metrics(r), metrics(r2)
    hist = [_dash(t) for t in r["trades"]] + ([_dash(o)] if o else [])
    t2 = r2["trades"] + ([r2["open"]] if r2["open"] else [])
    if len(t2) == len(hist):   # stessi segnali a 2x: PnL sul capitale per trade, per il simulatore della dashboard
        for h, t in zip(hist, t2):
            h["pnl2_pct"] = round(t["pnl"] * 100, 2)
    out["history"] = {"start": START, "trades": hist, "m1": m1, "m2": m2,
                      "final_10k_1x": round(float(r["equity"].iloc[-1]), 0), "final_10k_2x": round(float(r2["equity"].iloc[-1]), 0)}
    from .live import _clean
    return _clean(out)


# ---------------------------------------------------------------- eventi Telegram (dedupe sullo stato salvato)

def _usd(x: float) -> str:
    return f"${x:,.0f}".replace(",", ".")


def _pos_key(s: dict | None) -> str | None:
    """Chiave della posizione: data della domenica del segnale."""
    return (s or {}).get("signal_date") if (s or {}).get("status") in ("segnale", "aperto", "uscita") else None


def diff_events(cur: dict, prev: dict | None) -> tuple[list[dict], dict]:
    """(eventi nuovi, stato da salvare). prev=None = primo avvio dal vivo: la posizione già aperta si mostra
    come "in corso" con un solo messaggio informativo, senza rimandarla come segnale nuovo."""
    ev, k = [], _pos_key(cur)
    if prev is None:
        prev = {"notified": [k] if k and cur["status"] != "segnale" else [], "exits": []}
        if cur["status"] in ("aperto", "uscita"):
            ev.append({"type": "w_info", "w": cur})
            prev["trail_notified"] = cur.get("trail")
    st = {"notified": list(prev.get("notified", [])), "exits": list(prev.get("exits", [])),
          "trail_notified": prev.get("trail_notified"), "dist_week": prev.get("dist_week")}
    pk = _pos_key(prev) if prev.get("status") else None
    # uscita della posizione precedente (chiusa nello storico) o decisa per la prossima apertura
    if pk and pk not in st["exits"] and pk != k:
        t = next((x for x in cur["history"]["trades"] if x["signal"] == pk and x["reason"] != "open"), None)
        if t:
            ev.append({"type": "w_exit", "trade": t, "w": cur})
            st["exits"].append(pk)
    if cur["status"] == "uscita" and k not in st["exits"]:
        ev.append({"type": "w_exit_next", "w": cur})
        st["exits"].append(k)
    # segnale nuovo (anche se visto già entrato, se un giro è saltato)
    if k and k not in st["notified"]:
        ev.append({"type": "w_signal", "w": cur})
        st["notified"].append(k)
        st["trail_notified"] = cur["plan"]["stop"] if cur["status"] == "segnale" else cur.get("trail")
        st["dist_week"] = None
    elif cur["status"] == "aperto":
        tn, atr_d = st.get("trail_notified"), cur.get("atr_d") or 0.0
        if tn is None:
            st["trail_notified"] = cur["trail"]
        elif abs(cur["trail"] - tn) > atr_d:
            ev.append({"type": "w_trail", "w": cur, "old": tn})
            st["trail_notified"] = cur["trail"]
    if cur["status"] == "aperto" and cur.get("dist_now") and st.get("dist_week") != cur["week"]:
        ev.append({"type": "w_dist", "w": cur})
        st["dist_week"] = cur["week"]
    st.update(status=cur["status"], signal_date=cur.get("signal_date"), side=cur.get("side"), trail=cur.get("trail"),
              date=cur["date"])
    st["notified"], st["exits"] = st["notified"][-30:], st["exits"][-30:]
    return ev, st


def _exits_text(side: str) -> str:
    L = side == "long"
    return (f"Uscita alla prima: trailing 2,5 ATR settimanali dalla miglior chiusura giornaliera; chiusura settimanale "
            f"{'sotto' if L else 'sopra'} la EMA 21; distribuzione (funding medio 7g "
            + ("&gt; 0,09%/giorno con flusso perp negativo)." if L else "&lt; −0,03%/giorno con flusso perp positivo)."))


def _mkt(_w: dict, market: str, expo: float) -> str:
    return "SPOT 1x (niente leva, niente funding)" if market == "spot" else \
        f"PERP, esposizione {expo:.2f}x del capitale (tetto di rischio 25% allo stop), margine isolato"


def format_event(ev: dict) -> str:
    t, w = ev["type"], ev["w"]
    side = w.get("side") or ev.get("trade", {}).get("side", "")
    icon = "🟢 LONG" if side == "long" else "🔴 SHORT"
    if t == "w_signal":
        if w["status"] == "segnale":
            p = w["plan"]
            return "\n".join([
                f"<b>RADAR SIGNAL BTC · SEGNALE SETTIMANALE · {icon}</b> (W2)",
                f"Chiusura settimanale del {w['signal_date']}: {_usd(w['price'])} · regime {w['regime']} · flusso perp {w['flow']:+.2f}σ",
                f"<b>Ingresso</b> a mercato all'apertura di lunedì (~{_usd(p['entry_est'])})",
                f"<b>Mercato</b>: {_mkt(w, p['market'], p['expo'])}",
                f"<b>Su {_usd(p['capital'])}</b>: posizione {_usd(p['notional'])} = {p['btc']:.4f} BTC",
                f"<b>Stop iniziale</b> {_usd(p['stop'])} (2,5 ATR settimanali, −{p['stop_pct']:.1f}%) · perdita allo stop ~{_usd(p['loss_usd'])}",
                f"<b>Trailing</b>: {_usd(p['trail_dist'])} (2,5 ATRw) sotto/sopra la miglior chiusura giornaliera: ti avviso quando si sposta",
                f"<b>EMA 21 settimanale</b> {_usd(p['ema21'])}",
                _exits_text(w["side"]),
                "Operazioni rare (circa 3 l'anno) e lunghe: DD storico −42,6%."])
        return (f"<b>RADAR SIGNAL BTC · SEGNALE SETTIMANALE · {icon}</b> (W2, già in posizione)\n"
                f"Segnale del {w['signal_date']} · ingresso {w['entry']} a {_usd(w['entry_px'])} · mercato: {_mkt(w, w['market'], w['expo'])}\n"
                f"Trailing attuale {_usd(w['trail'])} · EMA 21 settimanale {_usd(w['ema21'])}\n" + _exits_text(w["side"]))
    if t == "w_info":
        return "\n".join([
            f"<b>RADAR SIGNAL BTC · Posizione settimanale in corso · {icon}</b> (W2)",
            "Da oggi il tool segue anche il segnale settimanale W2. Questa posizione è aperta dal "
            f"{w['entry']} a {_usd(w['entry_px'])}, non è un segnale nuovo. Mercato: {_mkt(w, w['market'], w['expo'])}.",
            f"Andamento {w['move_pct']:+.2f}% sul prezzo · trailing attuale {_usd(w['trail'])} · EMA 21 settimanale {_usd(w['ema21'])}",
            f"Su {_usd(w['capital'])}: {_usd(w['notional'])} = {w['btc']:.4f} BTC (se decidi di seguirla ora, entri a un prezzo diverso).",
            _exits_text(w["side"])])
    if t == "w_trail":
        return (f"<b>RADAR SIGNAL BTC · Settimanale: trailing aggiornato</b> ({w['side']})\n"
                f"Nuovo stop {_usd(w['trail'])} (era {_usd(ev['old'])}) · prezzo {_usd(w['price'])} · "
                f"andamento {w['move_pct']:+.2f}% sul prezzo")
    if t == "w_dist":
        return (f"<b>RADAR SIGNAL BTC · Settimanale: allerta distribuzione</b> ({w['side']})\n"
                f"Funding medio 7g {w['fund7'] * 100:+.4f}%/giorno · flusso perp {w['flow']:+.2f}σ. Se resta così alla chiusura "
                f"di domenica, la posizione si chiude lunedì all'apertura. Trailing {_usd(w['trail'])}.")
    if t == "w_exit_next":
        return (f"<b>RADAR SIGNAL BTC · USCITA SETTIMANALE</b> ({w['side']}) · all'apertura di lunedì\n"
                f"Motivo: {REASONS[w['reason']]} (chiusura del {w['exit_date']})\n"
                f"Ingresso {w['entry']} a {_usd(w['entry_px'])} · ora {_usd(w['price'])} · risultato stimato "
                f"{w['move_pct']:+.2f}% sul prezzo ({w['pnl_pct']:+.2f}% sul capitale dedicato)")
    if t == "w_exit":
        x = ev["trade"]
        return (f"<b>RADAR SIGNAL BTC · USCITA SETTIMANALE</b> ({x['side']}) {'✅' if x['pnl_pct'] > 0 else '❌'}\n"
                f"Motivo: {REASONS.get(x['reason'], x['reason'])} · uscita {x['exit']} a {_usd(x['exit_px'])}\n"
                f"Ingresso {x['entry']} a {_usd(x['entry_px'])} · risultato {x['move_pct']:+.2f}% sul prezzo "
                f"({x['pnl_pct']:+.2f}% sul capitale dedicato)")
    return str(ev)


# ---------------------------------------------------------------- controllo orario dello stop / trailing

def check_intraday(cur: dict, already: list[str], h: pd.DataFrame | None = None) -> tuple[list[dict], list[str]]:
    """Ogni ora: il trailing (o lo stop iniziale del segnale) è stato toccato sulle candele orarie dopo l'ultima
    chiusura giornaliera? Un'allerta per livello. `h` = candele orarie (test)."""
    if cur["status"] in ("aperto", "uscita"):
        level, sg = cur["trail"], 1 if cur["side"] == "long" else -1
    elif cur["status"] == "segnale":
        level, sg = cur["plan"]["stop"], 1 if cur["side"] == "long" else -1
    else:
        return [], already
    if h is None:
        from .intraday import hourly_since
        h = hourly_since(pd.Timestamp(cur["date"]) + pd.Timedelta(days=1))
    if h is None or h.empty:
        return [], already
    hit = float(h["low"].min()) <= level if sg > 0 else float(h["high"].max()) >= level
    key = f"W:{cur['signal_date']}:{level:.0f}"
    if not hit or key in already:
        return [], already
    return ([{"level": level, "side": cur["side"], "last": float(h["close"].iloc[-1]),
              "time": datetime.now(timezone.utc).strftime("%H:%M UTC")}], (list(already) + [key])[-30:])


def format_intraday(events: list[dict]) -> str:
    e = events[0]
    return (f"<b>RADAR SIGNAL BTC · Settimanale: stop toccato (tempo reale)</b> ({e['side']})\n"
            f"🛑 trailing/stop a {_usd(e['level'])} · prezzo ora {_usd(e['last'])} · {e['time']}\n"
            "Lo stop scatta al tocco: chiudi la posizione. L'uscita ufficiale si registra alla chiusura giornaliera.")
