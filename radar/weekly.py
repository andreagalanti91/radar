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
R_LONG = 0.25                      # W3 (12/11/2026): stesso tetto anche sui long (un long vicino a un top perdeva fino a −41%)
FLOW_N = 3                         # W3: flusso perp = media degli ultimi 3 giorni DISPONIBILI alla decisione (fino al sabato)
OLD_TREND, MACD_P = 16, (8, 21, 5)  # filtro F1 (01/11/2026): nei trend vecchi nuovo long solo con momentum MACD ripartito
FEE_SPOT, FEE_PERP, SLIP = 0.001, 0.0005, 0.001
CAPITAL = float(os.environ.get("RADAR_CAPITAL", "50000"))
SHARE = float(os.environ.get("RADAR_WEEKLY_SHARE", "1.0"))   # quota di RADAR_CAPITAL dedicata al settimanale
REASONS = {"trail": "trailing 2,5 ATR settimanali", "stop": "stop iniziale 2,5 ATR settimanali",
           "ema": "chiusura settimanale oltre la EMA 21", "dist": "distribuzione (funding e flusso perp)",
           "open": "posizione aperta"}


def live_flow(f: pd.DataFrame) -> pd.Series:
    """Flusso perp usato dalla strategia: media di FLOW_N giorni di pf14z, ritardata di un giorno. Alla chiusura della domenica
    il pf14z della domenica non c'è ancora (archivio Binance del giorno dopo): così backtest e segnale reale usano lo stesso dato."""
    return f["pf14z"].rolling(FLOW_N, min_periods=2).mean().shift(1)


def weekly_bars(f: pd.DataFrame) -> pd.DataFrame:
    """Candele settimanali W-SUN CHIUSE (solo settimane complete nei dati) con medie, ATR, flusso e funding."""
    w = f[["open", "high", "low", "close"]].resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    w["flow"] = live_flow(f).resample("W-SUN").last()          # W3: lo stesso dato dal vivo e nel backtest
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
    """Esposizione sul capitale con tetto di rischio allo stop iniziale (2,5 ATRw): 25% per long (W3) e short; il resto resta in liquidità."""
    return lev * min(1.0, (R_LONG if sg > 0 else R_SHORT) / (STOP_K * atr / close))


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
                tr["stop"] = tr["stop0"]
            pend = None
        if side:
            tl = tr["best"] - side * TRAIL_K * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)   # W3: a cricchetto, lo stop non si allenta mai
            tr["stop"] = stop
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
        trail = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)   # livello valido dal prossimo giorno (a cricchetto)
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
    wc = w[w.index >= pd.Timestamp(START) - pd.Timedelta(weeks=8)]   # grafico della dashboard: dal 2021 (con 8 settimane prima)
    wk, last = w.iloc[-1], f.iloc[-1]
    o, pd_ = r["open"], r["pending"]
    fund7 = float(f["funding"].fillna(0).rolling(7).mean().iloc[-1])
    flow = float(live_flow(f).dropna().iloc[-1])
    out = {"date": str(f.index[-1].date()), "week": str(w.index[-1].date()), "price": float(last["close"]),
           "atr_d": float(last["atr"]) if "atr" in f else None, "atr_w": float(wk["atr"]), "ema21": float(wk["ema21"]),
           "sma40": float(wk["sma"]), "ema20": float(wk["ema20"]), "flow": flow, "fund7": fund7,
           "regime": "long" if wk["close"] > wk["sma"] and wk["ema20"] > w["ema20"].iloc[-2] else
                     "short" if wk["close"] < wk["sma"] and wk["sma"] < w["sma"].iloc[-5] and wk["ema20"] < w["ema20"].iloc[-2]
                     else "neutro",
           "trend_age": int(wk["trend_age"]), "macd": float(wk["macd"]), "macd_sig": float(wk["macd_sig"]),
           "f1_ok": bool(wk["f1_ok"]), "old_trend": OLD_TREND,
           "ema20_up": bool(wk["ema20"] > w["ema20"].iloc[-2]),
           "chart": {k: [None if pd.isna(v) else round(float(v), 2) for v in wc[c]] for k, c in
                     (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("ema21", "ema21"), ("sma40", "sma"),
                      ("macd", "macd"), ("sig", "macd_sig"))} | {"d": [str(x.date()) for x in wc.index]},
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
    def _eq(r_):   # equity giornaliera da 1,0 (stessa curva delle Statistiche): il simulatore la usa per rendimento e drawdown
        e = r_["equity"] / r_["equity"].iloc[0]
        return [round(float(v), 5) for v in e.values]
    out["history"] = {"start": START, "trades": hist, "m1": m1, "m2": m2,
                      "eq_dates": [str(d.date()) for d in r["equity"].index], "eq1": _eq(r), "eq2": _eq(r2),
                      "final_10k_1x": round(float(r["equity"].iloc[-1]), 0), "final_10k_2x": round(float(r2["equity"].iloc[-1]), 0)}
    from .live import _clean
    return _clean(out)



# ---------------------------------------------------------------- eventi Telegram (dedupe sullo stato salvato)
#
# Ogni evento porta le sue "marcature" (ev["mark"]): si applicano allo stato SOLO se Telegram conferma l'invio
# (send_events). Un invio fallito lascia lo stato com'era e l'evento si ripropone al giro dopo.
# Chiavi separate (data della domenica del segnale):
#   notified        segnale annunciato          entered    ingresso eseguito comunicato
#   exit_announced  uscita annunciata (lunedì)  exit_done  uscita eseguita comunicata (prezzo reale e risultato)
#   pending_signal / pending_exit: annunci non ancora eseguiti, da ritirare se i dati rivisti non li confermano più
#   trail_notified / trail_sig: ultimo stop comunicato all'utente e posizione a cui si riferisce

TRAIL_STEP = 0.005     # nuovo avviso del trailing quando sale (long) / scende (short) di almeno lo 0,5% del prezzo
RECENT_DAYS = 7        # ingressi/uscite più vecchi di così (giri saltati a lungo, primo avvio) si registrano senza messaggio
W3_TEXT = "Operazioni rare (13 trade dal 2021, circa 2 l'anno) e lunghe · DD massimo storico −21% · " \
          "al massimo il 25% del capitale a rischio allo stop iniziale."


def _usd(x: float) -> str:
    return f"${x:,.0f}".replace(",", ".")


def _pos_key(s: dict | None) -> str | None:
    """Chiave della posizione: data della domenica del segnale."""
    return (s or {}).get("signal_date") if (s or {}).get("status") in ("segnale", "aperto", "uscita") else None


def _sg(side: str | None) -> int:
    return 1 if side == "long" else -1


def _norm_state(prev: dict) -> dict:
    """Stato salvato -> stato di lavoro (con migrazione dal formato a una sola lista "exits")."""
    old = "exit_done" not in prev
    return {"notified": list(prev.get("notified", [])),
            # vecchio formato: "exits" mescolava uscita annunciata ed eseguita -> annunciata; la conferma eseguita
            # (prezzo reale e risultato) parte ancora se l'uscita è recente
            "exit_announced": list(prev.get("exit_announced", prev.get("exits", []))),
            "exit_done": list(prev.get("exit_done", [])),
            "entered": list(prev.get("entered", prev.get("notified", []) if old else [])),
            "pending_signal": prev.get("pending_signal"), "pending_exit": prev.get("pending_exit"),
            "trail_notified": prev.get("trail_notified"),
            "trail_sig": prev.get("trail_sig", prev.get("signal_date") if old else None),
            "dist_week": prev.get("dist_week"), "side": prev.get("side")}


def apply_marks(st: dict, ev: dict) -> dict:
    """Applica allo stato le marcature di un evento inviato con successo."""
    for op, field, val in ev.get("mark", []):
        if op == "add":
            if val not in st.setdefault(field, []):
                st[field].append(val)
            st[field] = st[field][-30:]
        elif op == "remove":
            st[field] = [x for x in st.get(field, []) if x != val]
        else:
            st[field] = val
    return st


def _recent(day: str | None, today: str) -> bool:
    return bool(day) and (pd.Timestamp(today) - pd.Timestamp(day)).days <= RECENT_DAYS


def _why_not_signal(cur: dict, side: str | None) -> str:
    """Perché un segnale annunciato non è più valido sui dati attuali (W3: regime, EMA 21, flusso, filtro MACD)."""
    why, L = [], side == "long"
    c = (cur.get("chart") or {}).get("c") or [None]
    close = c[-1]
    if cur.get("regime") != side:
        why.append(f"regime settimanale ora {cur.get('regime')}")
    if close is not None and cur.get("ema21") is not None and ((close <= cur["ema21"]) if L else (close >= cur["ema21"])):
        why.append(f"chiusura settimanale {_usd(close)} {'sotto' if L else 'sopra'} la EMA 21 ({_usd(cur['ema21'])})")
    if cur.get("flow") is not None and ((cur["flow"] <= 0) if L else (cur["flow"] >= 0)):
        why.append(f"flusso perp ora {cur['flow']:+.2f}σ")
    if L and cur.get("f1_ok") is False:
        why.append("filtro MACD dei trend vecchi non soddisfatto")
    return "; ".join(why) or "i dati rivisti non confermano più la decisione"


def pending_events(cur: dict, prev: dict | None) -> tuple[list[dict], dict]:
    """(eventi da inviare, stato di base). Lo stato di base NON contiene le marcature degli eventi: si aggiungono
    con apply_marks solo dopo un invio riuscito. prev=None = primo avvio dal vivo: la posizione già aperta si mostra
    come "in corso" con un solo messaggio informativo, senza rimandarla come segnale nuovo."""
    ev, k, status = [], _pos_key(cur), cur["status"]
    trades = cur.get("history", {}).get("trades", [])
    by_sig = {t["signal"]: t for t in trades}
    first = prev is None
    st = _norm_state(prev or {})
    if first and status in ("aperto", "uscita"):
        ev.append({"type": "w_info", "w": cur, "mark": [("add", "notified", k), ("add", "entered", k),
                                                       ("set", "trail_notified", cur.get("trail")), ("set", "trail_sig", k)]})
    # 1. annunci ritirati: segnale (ingresso di lunedì) o uscita non più validi dopo una revisione dei dati
    ps = st.get("pending_signal")
    if ps and ps not in by_sig and not (status == "segnale" and k == ps):
        ev.append({"type": "w_retract", "kind": "signal", "w": cur, "key": ps, "side": st.get("side"),
                   "why": _why_not_signal(cur, st.get("side")),
                   "mark": [("set", "pending_signal", None), ("remove", "notified", ps)]})
    pe = st.get("pending_exit")
    pe_closed = pe in by_sig and by_sig[pe]["reason"] != "open"
    if pe and not pe_closed and not (status == "uscita" and k == pe):
        ev.append({"type": "w_retract", "kind": "exit", "w": cur, "key": pe, "side": st.get("side"),
                   "why": ("la posizione resta aperta: la chiusura settimanale non conferma più l'uscita"
                           if k == pe else "la posizione non risulta più nello storico ricalcolato"),
                   "mark": [("set", "pending_exit", None), ("remove", "exit_announced", pe)]})
    # 2. uscite eseguite (dallo storico, con il prezzo reale di uscita e il risultato)
    known = set(st["notified"]) | set(st["entered"]) | set(st["exit_announced"])
    for t in trades:
        s = t["signal"]
        if t["reason"] == "open" or s not in known or s in st["exit_done"]:
            continue
        mark = [("add", "exit_done", s), ("add", "exit_announced", s)] + \
               ([("set", "pending_exit", None)] if st.get("pending_exit") == s else [])
        if _recent(t["exit"], cur["date"]):
            ev.append({"type": "w_exit", "trade": t, "w": cur, "mark": mark})
        else:
            apply_marks(st, {"mark": mark})
    # 3. uscita decisa per la prossima apertura
    if status == "uscita" and k not in st["exit_announced"] and k not in st["exit_done"]:
        ev.append({"type": "w_exit_next", "w": cur, "mark": [("add", "exit_announced", k), ("set", "pending_exit", k)]})
    # 4. segnale nuovo (ingresso all'apertura di lunedì)
    if status == "segnale" and k not in st["notified"]:
        ev.append({"type": "w_signal", "w": cur, "mark": [
            ("add", "notified", k), ("set", "pending_signal", k), ("set", "trail_notified", cur["plan"]["stop"]),
            ("set", "trail_sig", k), ("set", "dist_week", None), ("set", "side", cur.get("side"))]})
    # 5. ingressi eseguiti di segnali annunciati
    for t in trades:
        s = t["signal"]
        if s not in st["notified"] or s in st["entered"]:
            continue
        mark = [("add", "entered", s)] + ([("set", "pending_signal", None)] if st.get("pending_signal") == s else [])
        if _recent(t["entry"], cur["date"]):
            ev.append({"type": "w_entry", "trade": t, "w": cur, "mark": mark})
        else:
            apply_marks(st, {"mark": mark})
    # 6. posizione aperta mai annunciata (giri saltati durante il segnale): segnale "già in posizione"
    if not first and status in ("aperto", "uscita") and k not in st["notified"]:
        ev.append({"type": "w_signal", "w": cur, "mark": [
            ("add", "notified", k), ("add", "entered", k), ("set", "trail_notified", cur.get("trail")),
            ("set", "trail_sig", k), ("set", "dist_week", None), ("set", "side", cur.get("side"))]})
    # 7. trailing (W3, a cricchetto): avviso quando il livello migliora di almeno lo 0,5% del prezzo
    elif status == "aperto" and k in st["notified"]:
        tn = st.get("trail_notified")
        if tn is None or st.get("trail_sig") != k:
            st["trail_notified"], st["trail_sig"] = cur["trail"], k
        elif (cur["trail"] - tn) * _sg(cur.get("side")) >= TRAIL_STEP * cur["price"]:
            ev.append({"type": "w_trail", "w": cur, "old": tn,
                       "mark": [("set", "trail_notified", cur["trail"]), ("set", "trail_sig", k)]})
    if status == "aperto" and cur.get("dist_now") and st.get("dist_week") != cur["week"]:
        ev.append({"type": "w_dist", "w": cur, "mark": [("set", "dist_week", cur["week"])]})
    st.update(status=status, signal_date=cur.get("signal_date"), trail=cur.get("trail"), date=cur["date"],
              side=(cur.get("side") or st.get("side")) if status != "nessuno" else st.get("side"))
    return ev, st


def diff_events(cur: dict, prev: dict | None) -> tuple[list[dict], dict]:
    """(eventi nuovi, stato con tutti gli eventi marcati come inviati). Per l'invio reale usare send_events,
    che marca solo gli eventi confermati da Telegram."""
    ev, st = pending_events(cur, prev)
    for e in ev:
        apply_marks(st, e)
    return ev, st


def send_events(cur: dict, prev: dict | None, send) -> tuple[list[dict], dict]:
    """Invia gli eventi uno per uno (send(text) -> message_id/True se riuscito, False/None se no) e marca nello
    stato solo quelli riusciti. Restituisce (eventi inviati, stato da salvare). Un errore di formattazione o di
    rete su un evento non blocca gli altri."""
    ev, st = pending_events(cur, prev)
    sent = []
    for e in ev:
        try:
            ok = send(format_event(e))
        except Exception as x:  # noqa: BLE001
            print(f"[weekly] evento {e['type']} non inviato: {x!r}")
            ok = False
        if ok:
            apply_marks(st, e)
            sent.append(e)
        else:
            print(f"[weekly] evento {e['type']} non confermato da Telegram: si riprova al prossimo giro")
    return sent, st


def _exits_text(side: str) -> str:
    L = side == "long"
    return (f"Uscita alla prima: trailing 2,5 ATR settimanali dalla miglior chiusura giornaliera (a cricchetto, non scende mai); "
            f"chiusura settimanale {'sotto' if L else 'sopra'} la EMA 21; distribuzione (funding medio 7g "
            + ("&gt; 0,09%/giorno con flusso perp negativo)." if L else "&lt; −0,03%/giorno con flusso perp positivo)."))


def _mkt(_w: dict, market: str, expo: float) -> str:
    return f"SPOT, esposizione {expo:.2f}x (niente leva, niente funding)" if market == "spot" else \
        f"PERP, esposizione {expo:.2f}x del capitale (tetto di rischio 25% allo stop), margine isolato"


def format_event(ev: dict) -> str:
    t, w = ev["type"], ev["w"]
    side = ev.get("side") or w.get("side") or ev.get("trade", {}).get("side", "")
    icon = "🟢 LONG" if side == "long" else "🔴 SHORT"
    if t == "w_signal":
        if w["status"] == "segnale":
            p = w["plan"]
            return "\n".join([
                f"<b>RADAR SIGNAL BTC · SEGNALE SETTIMANALE · {icon}</b> (W3)",
                f"Chiusura settimanale del {w['signal_date']}: {_usd(w['price'])} · regime {w['regime']} · flusso perp {w['flow']:+.2f}σ",
                f"<b>Ingresso</b> a mercato all'apertura di lunedì (~{_usd(p['entry_est'])}): ti confermo il prezzo eseguito",
                f"<b>Mercato</b>: {_mkt(w, p['market'], p['expo'])}",
                f"<b>Su {_usd(p['capital'])}</b>: posizione {_usd(p['notional'])} = {p['btc']:.4f} BTC",
                f"<b>Stop iniziale</b> {_usd(p['stop'])} (2,5 ATR settimanali, −{p['stop_pct']:.1f}%) · perdita allo stop ~{_usd(p['loss_usd'])}",
                f"<b>Trailing</b>: {_usd(p['trail_dist'])} (2,5 ATRw) dalla miglior chiusura giornaliera: ti avviso quando "
                f"sale di almeno lo 0,5% del prezzo",
                f"<b>EMA 21 settimanale</b> {_usd(p['ema21'])}",
                _exits_text(w["side"]),
                W3_TEXT])
        return (f"<b>RADAR SIGNAL BTC · SEGNALE SETTIMANALE · {icon}</b> (W3, già in posizione)\n"
                f"Segnale del {w['signal_date']} · ingresso {w['entry']} a {_usd(w['entry_px'])} · mercato: {_mkt(w, w['market'], w['expo'])}\n"
                f"Stop/trailing attuale {_usd(w['trail'])} · EMA 21 settimanale {_usd(w['ema21'])}\n" + _exits_text(w["side"]))
    if t == "w_entry":
        x = ev["trade"]
        lines = [f"<b>RADAR SIGNAL BTC · INGRESSO SETTIMANALE ESEGUITO · {icon}</b> (W3)",
                 f"Segnale del {x['signal']} · ingresso {x['entry']} all'apertura a <b>{_usd(x['entry_px'])}</b> · "
                 f"mercato: {_mkt(w, x['market'], x['expo'])}"]
        if w.get("status") in ("aperto", "uscita") and w.get("signal_date") == x["signal"]:
            lines.append(f"Su {_usd(w['capital'])}: {_usd(w['notional'])} = {w['btc']:.4f} BTC · stop iniziale {_usd(w['stop0'])} · "
                         f"stop/trailing attuale {_usd(w['trail'])} · prezzo ora {_usd(w['price'])}")
        elif x.get("reason") != "open":
            lines.append(f"Posizione già chiusa: uscita {x['exit']} a {_usd(x['exit_px'])} ({REASONS.get(x['reason'], x['reason'])})")
        return "\n".join(lines)
    if t == "w_info":
        return "\n".join([
            f"<b>RADAR SIGNAL BTC · Posizione settimanale in corso · {icon}</b> (W3)",
            "Da oggi il tool segue anche il segnale settimanale W3. Questa posizione è aperta dal "
            f"{w['entry']} a {_usd(w['entry_px'])}, non è un segnale nuovo. Mercato: {_mkt(w, w['market'], w['expo'])}.",
            f"Andamento {w['move_pct']:+.2f}% sul prezzo · stop/trailing attuale {_usd(w['trail'])} · EMA 21 settimanale {_usd(w['ema21'])}",
            f"Su {_usd(w['capital'])}: {_usd(w['notional'])} = {w['btc']:.4f} BTC (se decidi di seguirla ora, entri a un prezzo diverso).",
            _exits_text(w["side"])])
    if t == "w_trail":
        return (f"<b>RADAR SIGNAL BTC · Settimanale: trailing aggiornato</b> ({w['side']}, W3)\n"
                f"Nuovo stop {_usd(w['trail'])} (era {_usd(ev['old'])}) · prezzo {_usd(w['price'])} · "
                f"andamento {w['move_pct']:+.2f}% sul prezzo")
    if t == "w_dist":
        return (f"<b>RADAR SIGNAL BTC · Settimanale: allerta distribuzione</b> ({w['side']}, W3)\n"
                f"Funding medio 7g {w['fund7'] * 100:+.4f}%/giorno · flusso perp {w['flow']:+.2f}σ. Se resta così alla chiusura "
                f"di domenica, la posizione si chiude lunedì all'apertura. Trailing {_usd(w['trail'])}.")
    if t == "w_exit_next":
        return (f"<b>RADAR SIGNAL BTC · USCITA SETTIMANALE ANNUNCIATA</b> ({w['side']}, W3) · all'apertura di lunedì\n"
                f"Motivo: {REASONS[w['reason']]} (chiusura del {w['exit_date']})\n"
                f"Ingresso {w['entry']} a {_usd(w['entry_px'])} · ora {_usd(w['price'])} · risultato stimato "
                f"{w['move_pct']:+.2f}% sul prezzo ({w['pnl_pct']:+.2f}% sul capitale dedicato). "
                f"Ti confermo prezzo eseguito e risultato dopo l'apertura.")
    if t == "w_exit":
        x = ev["trade"]
        return (f"<b>RADAR SIGNAL BTC · USCITA SETTIMANALE ESEGUITA</b> ({x['side']}, W3) {'✅' if x['pnl_pct'] > 0 else '❌'}\n"
                f"Motivo: {REASONS.get(x['reason'], x['reason'])} · uscita {x['exit']} a <b>{_usd(x['exit_px'])}</b>\n"
                f"Ingresso {x['entry']} a {_usd(x['entry_px'])} · risultato {x['move_pct']:+.2f}% sul prezzo "
                f"(<b>{x['pnl_pct']:+.2f}%</b> sul capitale dedicato)")
    if t == "w_retract":
        if ev["kind"] == "signal":
            return (f"<b>RADAR SIGNAL BTC · SEGNALE SETTIMANALE RITIRATO</b> ({side}, W3, segnale del {ev['key']})\n"
                    f"Dopo l'aggiornamento dei dati il segnale non è più valido: {ev['why']}.\n"
                    "Nessun ingresso: se sei già entrato, valuta di chiudere. Stato attuale: "
                    + ("nessuna posizione." if w["status"] == "nessuno" else f"{w['status']}."))
        return (f"<b>RADAR SIGNAL BTC · USCITA SETTIMANALE RITIRATA</b> ({side}, W3, segnale del {ev['key']})\n"
                f"Dopo l'aggiornamento dei dati l'uscita annunciata non è più valida: {ev['why']}."
                + (f"\nStop/trailing {_usd(w['trail'])} · EMA 21 settimanale {_usd(w['ema21'])}" if w.get("trail") else ""))
    return str(ev)


def next_decision(today: str | pd.Timestamp) -> str:
    """Prossima decisione W3: chiusura UTC della domenica (oggi se è domenica)."""
    d = pd.Timestamp(today).normalize()
    return str((d + pd.Timedelta(days=(6 - d.dayofweek) % 7)).date())


def _state_word(cur: dict | None) -> str:
    if not cur:
        return "non calcolato"
    s = cur.get("status")
    if s == "aperto":
        return f"{cur['side']} aperto, stop {_usd(cur['trail'])}"
    if s == "uscita":
        return f"{cur['side']}, uscita lunedì all'apertura"
    if s == "segnale":
        return f"segnale {cur['side']}, ingresso lunedì all'apertura"
    return f"nessuna posizione (regime {cur.get('regime')})"


def format_heartbeat(cur: dict | None, data_until: str, last_run: str, problems: list[str], today: str) -> str:
    """Messaggio quotidiano di salute (uno al giorno): dati, ultimo giro, stato W3, prossima decisione."""
    head = "Radar · tutto ok" if not problems else "Radar · attenzione: " + "; ".join(problems)
    return (f"{head}: dati fino al {data_until}, ultimo giro {last_run}, W3 {_state_word(cur)}, "
            f"prossima decisione {next_decision(today)} (chiusura UTC)")


# ---------------------------------------------------------------- controllo orario dello stop / trailing

def told_level(st: dict | None, cur: dict) -> float | None:
    """Ultimo stop comunicato all'utente per la posizione attuale (None se riferito a un'altra posizione)."""
    st = st or {}
    return st.get("trail_notified") if st.get("trail_sig") and st.get("trail_sig") == cur.get("signal_date") else None


def check_intraday(cur: dict, already: list[str], h: pd.DataFrame | None = None,
                   told: float | None = None) -> tuple[list[dict], list[str]]:
    """Ogni ora: lo stop è stato toccato sulle candele orarie dopo l'ultima chiusura giornaliera? Livello controllato =
    il più protettivo tra quello del modello (trailing W3 o stop iniziale del segnale) e l'ultimo comunicato
    all'utente (`told`): l'allerta non arriva mai dopo il livello che l'utente conosce. Un'allerta per livello.
    `h` = candele orarie (test). Le chiavi restituite vanno salvate solo se l'invio riesce."""
    if cur["status"] in ("aperto", "uscita"):
        model = cur["trail"]
    elif cur["status"] == "segnale":
        model = cur["plan"]["stop"]
    else:
        return [], already
    sg = _sg(cur["side"])
    level = model if told is None else (max(model, told) if sg > 0 else min(model, told))
    if h is None:
        from .intraday import hourly_since
        h = hourly_since(pd.Timestamp(cur["date"]) + pd.Timedelta(days=1))
    if h is None or h.empty:
        return [], already
    hit = float(h["low"].min()) <= level if sg > 0 else float(h["high"].max()) >= level
    key = f"W:{cur['signal_date']}:{level:.0f}"
    if not hit or key in already:
        return [], already
    if told is None:
        which = "modello"
    elif abs(told - model) < 0.5:
        which = "comunicato = modello"
    else:
        which = "comunicato" if level == told else "modello"
    return ([{"level": level, "model": model, "told": told, "which": which, "side": cur["side"],
              "last": float(h["close"].iloc[-1]), "time": datetime.now(timezone.utc).strftime("%H:%M UTC")}],
            (list(already) + [key])[-30:])


def format_intraday(events: list[dict]) -> str:
    e = events[0]
    if e.get("which") == "comunicato":
        lvl = f"stop comunicato {_usd(e['level'])} (livello del modello {_usd(e['model'])})"
    elif e.get("told") is not None and e.get("which") == "modello":
        lvl = f"stop del modello {_usd(e['level'])} (ultimo comunicato {_usd(e['told'])})"
    else:
        lvl = f"stop {_usd(e['level'])}"
    return (f"<b>RADAR SIGNAL BTC · Settimanale: stop toccato (tempo reale)</b> ({e['side']}, W3)\n"
            f"🛑 toccato lo {lvl} · prezzo ora {_usd(e['last'])} · {e['time']}\n"
            "Lo stop scatta al tocco: chiudi la posizione. L'uscita ufficiale si registra alla chiusura giornaliera.")
