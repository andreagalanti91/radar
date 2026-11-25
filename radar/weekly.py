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
  min(1, 0,25 / (2,5·ATRw/close)) = tetto di rischio del 25% allo stop (W3.2 dal 22/11/2026, scelta dell'utente; W3.1 era 0,10) (commissione 0,05%/lato, funding reale).
  Slippage 0,1%. Il tetto sugli short è stato scelto dopo i risultati (ricerca W5), per prudenza.
Motore di riferimento della ricerca: /tmp/radar-work/w5/scripts/sim3.py (W2 V1, R=0,25, solo short), riscritto qui
senza le varianti non usate. Stato dal vivo in data/state.json (chiave "weekly"), eventi Telegram con dedupe.
Importi su RADAR_CAPITAL × RADAR_WEEKLY_SHARE (quota del capitale dedicata al settimanale: la sceglie l'utente).
"""
from __future__ import annotations

import os
import re
from datetime import datetime, timezone

import numpy as np
import pandas as pd

from . import telegram as tg

START = "2021-01-01"
LIVE_START = "2026-10-31"
SMA, EMA_T, EMA_X, ATR_N = 40, 20, 21, 14
STOP_K = TRAIL_K = 2.5
FUND_HOT, FUND_COLD = 0.0009, -0.0003
R_SHORT = 0.25                     # W3.2 (22/11/2026, scelta esplicita dell'utente: DD 20–30%, rendimento massimo): rischio allo stop 25% (W3.1: 10%)
R_LONG = 0.25                      # W3.2: stesso rischio sui long; uno stop pieno costa ~25% della quota (lezione 99)
FLOW_N = 3                         # W3: flusso perp = media degli ultimi 3 giorni DISPONIBILI alla decisione (fino al sabato)
OLD_TREND, MACD_P = 16, (8, 21, 5)  # filtro F1 (01/11/2026): nei trend vecchi nuovo long solo con momentum MACD ripartito
FEE_SPOT, FEE_PERP, SLIP = 0.001, 0.0005, 0.001


def _env_float(name: str, default: float) -> float:
    """Numero da variabile d'ambiente, tollerante: virgola decimale, spazi, vuoto -> default. Un valore non valido
    (o non positivo) usa il default con un messaggio nel log: mai un'eccezione all'import (fermerebbe tutto il giro)."""
    raw = os.environ.get(name)
    if raw is None or not raw.strip():
        return default
    txt = raw.strip().replace(" ", "").replace("\u00a0", "")
    if "," in txt:
        txt = txt.replace(".", "").replace(",", ".") if "." in txt else txt.replace(",", ".")   # 50.000,5 / 0,5
    elif re.fullmatch(r"\d{1,3}(\.\d{3})+", txt):
        txt = txt.replace(".", "")   # 50.000 / 1.250.000: punto delle migliaia all'italiana (mai un decimale a 3 cifre)
    try:
        v = float(txt)
        if not np.isfinite(v) or v <= 0:
            raise ValueError("non positivo")
        return v
    except ValueError:
        print(f"[weekly] {name}={raw!r} non valido: uso il valore predefinito {default}")
        return default


CAPITAL = _env_float("RADAR_CAPITAL", 30000.0)   # capitale reale dichiarato dall'utente il 23/11/2026: 30.000 $ su BTC
SHARE = _env_float("RADAR_WEEKLY_SHARE", 1.0)   # quota di RADAR_CAPITAL dedicata al settimanale


def _env_share(name: str, default: float) -> float:
    """Quota da variabile d'ambiente fra 0 (incluso: asset escluso) e 1 (escluso), tollerante come _env_float."""
    raw = os.environ.get(name)
    if raw is not None and raw.strip() in ("0", "0,0", "0.0"):
        return 0.0
    v = _env_float(name, default)
    if v >= 1:
        print(f"[weekly] {name}={raw!r} deve essere minore di 1: uso il valore predefinito {default}")
        return default
    return v


# Asset di W3.2 (decisione dell'utente del 22/11/2026: "Mantieni ETH nella strategia, inserisci dentro il Tool"; poi "non suddividere
# 70-30: 10k su ETH, 10k su BTC"): stesse regole e parametri su ogni asset, ciascuno con il SUO capitale separato e il rischio 25%
# allo stop su quel capitale. BTC = RADAR_CAPITAL × RADAR_WEEKLY_SHARE (come prima di ETH); ETH = RADAR_ETH_CAPITAL (predefinito
# 30.000 $). Le percentuali dello storico non dipendono dal capitale; cambiano solo i dollari.
ASSET_LIST = ("BTC", "ETH")
ETH_CAPITAL = _env_float("RADAR_ETH_CAPITAL", 30000.0)   # 30.000 $ su ETH (utente, 23/11/2026)
ASSET_SHARE = {"BTC": 1.0, "ETH": None}   # nessuna suddivisione: capitali separati
ASSET_LIVE_START = {"BTC": LIVE_START, "ETH": "2026-11-22"}


def asset_capital(asset: str = "BTC", capital: float | None = None, share: float | None = None) -> float:
    """Dollari dedicati all'asset (capitali separati): BTC = RADAR_CAPITAL × RADAR_WEEKLY_SHARE, ETH = RADAR_ETH_CAPITAL.
    `capital` esplicito sostituisce il valore configurato; `share` resta per compatibilità (moltiplica `capital`)."""
    if capital is None:
        capital = ETH_CAPITAL if asset == "ETH" else CAPITAL * SHARE
    return capital * (1.0 if share is None else share)


def asset_of(x: dict | None) -> str:
    return (x or {}).get("asset") or "BTC"
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
    """Esposizione sul capitale con tetto di rischio allo stop iniziale (2,5 ATRw): 25% per long e short (W3.2); il resto resta in liquidità."""
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


def plan(side: int, close: float, atr: float, ema21: float, capital: float, asset: str = "BTC") -> dict:
    """Piano in dollari per un ingresso: mercato, esposizione, quantità, stop iniziale, perdita allo stop."""
    ex = exposure(side, close, atr)
    stop = close - side * STOP_K * atr
    stop_pct = STOP_K * atr / close
    notional = capital * ex
    return {"market": "spot" if side > 0 else "perp", "expo": round(ex, 3), "capital": round(capital, 0),
            "notional": round(notional, 0), "qty": round(notional / close, 4), "entry_est": round(close, 2),
            "stop": round(stop, 2), "stop_pct": round(stop_pct * 100, 2),
            "loss_usd": round(notional * (stop_pct + SLIP + 2 * (FEE_SPOT if side > 0 else FEE_PERP)), 0),
            "trail_dist": round(TRAIL_K * atr, 2), "ema21": round(ema21, 2)} | \
        ({"btc": round(notional / close, 4)} if asset == "BTC" else {})


def exits_block(side: str, entry_px: float, price: float, best: float, trail: float, atr_w: float, ema21: float,
                expo: float, capital: float, pnl_pct: float, fund7: float, flow: float) -> dict:
    """Solo descrittivo (nessun effetto su segnali e uscite): per ciascuna delle tre uscite di W3.2 il livello, l'esito se
    scattasse ora rispetto all'ingresso (costi come in simulate: slippage e commissione d'uscita, funding già pagato incluso
    in pnl_pct) e la soglia oltre la quale diventa un'uscita in profitto. Percentuali in punti %, dollari sul capitale dell'asset."""
    sg = 1 if side == "long" else -1
    fee = FEE_SPOT if sg > 0 else FEE_PERP

    def at(x: float) -> dict:   # esito se si esce al prezzo x
        xs = x * (1 - SLIP * sg)
        cap = pnl_pct / 100 + sg * expo * (xs - price) / entry_px - expo * xs / entry_px * fee
        return {"pct_price": round(sg * (x / entry_px - 1) * 100, 2), "pct_cap": round(cap * 100, 2),
                "usd": round(capital * cap, 0), "esito": "profitto" if cap > 0 else "perdita"}

    thr = entry_px + sg * TRAIL_K * atr_w      # miglior chiusura oltre la quale il trailing passa dal lato del profitto
    tr = {"level": round(trail, 2), "check": "ogni ora", "atr_w": round(atr_w, 2), "best": round(best, 2),
          "soglia": round(thr, 2), "soglia_dist_pct": round((thr / price - 1) * 100, 2),
          "soglia_ok": bool(sg * (trail - entry_px) > 0)} | at(trail)
    em = {"level": round(ema21, 2), "check": "chiusura settimanale", "soglia": round(entry_px, 2),
          "soglia_dist_pct": round((entry_px / ema21 - 1) * 100, 2), "soglia_ok": bool(sg * (ema21 - entry_px) > 0),
          "settimane": None} | at(ema21)
    # stima onesta solo nel caso semplice: prezzo fermo già dal lato del profitto, la EMA 21 (α = 2/22) gli si avvicina
    # di una frazione fissa a settimana: settimane perché passi l'ingresso
    if not em["soglia_ok"] and sg * (price - entry_px) > 0:
        a = 2 / (EMA_X + 1)
        em["settimane"] = int(np.ceil(np.log((entry_px - price) / (ema21 - price)) / np.log(1 - a)))
    hot = fund7 > FUND_HOT if sg > 0 else fund7 < FUND_COLD
    fl = flow < 0 if sg > 0 else flow > 0
    di = {"check": "chiusura della domenica", "fund7": fund7, "fund_soglia": FUND_HOT if sg > 0 else FUND_COLD,
          "fund_ok": bool(hot), "flow": flow, "flow_ok": bool(fl), "attiva": bool(hot and fl)} | at(price)
    return {"side": side, "entry_px": round(entry_px, 2), "price": round(price, 2), "trail": tr, "ema21": em, "dist": di,
            "calc": {"sg": sg, "expo": expo, "fee": fee, "slip": SLIP, "pnl_pct": pnl_pct, "px0": round(price, 2),
                     "capital": round(capital, 0)}}


def evaluate(f: pd.DataFrame, capital: float | None = None, asset: str = "BTC") -> dict:
    """Stato attuale W3.2 di un asset: nessuno / segnale (ingresso alla prossima apertura) / aperto / uscita (alla prossima
    apertura), con livelli e piano in dollari, più lo storico dal 2021 a 1x e 2x. `capital` = dollari dedicati all'asset
    (predefinito asset_capital(asset)); le regole non dipendono dall'asset."""
    capital = asset_capital(asset) if capital is None else capital
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
           "sma40_dn": bool(wk["sma"] < w["sma"].iloc[-5]), "sma40_4w": float(w["sma"].iloc[-5]),
           "chart": {k: [None if pd.isna(v) else round(float(v), 2) for v in wc[c]] for k, c in
                     (("o", "open"), ("h", "high"), ("l", "low"), ("c", "close"), ("ema21", "ema21"), ("sma40", "sma"),
                      ("macd", "macd"), ("sig", "macd_sig"))} | {"d": [str(x.date()) for x in wc.index]},
           "capital": round(capital, 0), "share": SHARE, "asset": asset, "asset_share": ASSET_SHARE.get(asset),
           "status": "nessuno"}
    if o:
        sg = 1 if o["side"] == "long" else -1
        out.update(status="aperto", side=o["side"], signal_date=o["signal"], entry=o["entry"], entry_px=o["entry_px"],
                   market=o["market"], expo=o["expo"], stop0=round(o["stop0"], 2), trail=round(o["trail"], 2),
                   best=round(float(o["best"]), 2), move_pct=round(o["move"] * 100, 2), pnl_pct=round(o["pnl"] * 100, 2),
                   notional=round(capital * o["expo"], 0), qty=round(capital * o["expo"] / o["entry_px"], 4),
                   dist_now=bool((fund7 > FUND_HOT and flow < 0) if sg > 0 else (fund7 < FUND_COLD and flow > 0)),
                   trail_usd=round(capital * o["expo"] * (o["trail"] / o["entry_px"] - 1) * sg, 0))
        if asset == "BTC":
            out["btc"] = out["qty"]
        out["uscite"] = exits_block(o["side"], o["entry_px"], float(last["close"]), float(o["best"]), float(o["trail"]),
                                    float(o["curatr"]), float(wk["ema21"]), o["expo"], capital, out["pnl_pct"], fund7, flow)
        if pd_ and pd_["kind"] == "exit":
            out.update(status="uscita", reason=pd_["arg"], exit_date=pd_["date"])
    elif pd_ and pd_["kind"] == "enter":
        sg = pd_["arg"]
        out.update(status="segnale", side="long" if sg > 0 else "short", signal_date=pd_["date"],
                   plan=plan(sg, float(wk["close"]), float(wk["atr"]), float(wk["ema21"]), capital, asset))
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
W3_TEXT = "Operazioni rare (13 dal 2021, circa 2 l'anno) e lunghe · calo massimo storico −21% · al massimo il 25% " \
          "del capitale a rischio allo stop iniziale."
W3_TEXTS = {"BTC": W3_TEXT,
            "ETH": "Operazioni rare (15 dal 2021, circa 2–3 l'anno) · calo massimo storico −27,5% · 60% dei trade in "
                   "profitto · al massimo il 25% della quota ETH a rischio allo stop iniziale."}


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
            "dist_week": prev.get("dist_week"), "side": prev.get("side"),
            "restore_pending": bool(prev.get("restore_pending"))}


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


def state_lost(cur: dict, prev: dict | None) -> bool:
    """Stato degli avvisi assente con il tool già in funzione dal vivo (dati successivi all'avvio dal vivo dell'asset,
    ASSET_LIVE_START): state.json illeggibile, cancellato o senza la chiave "weekly". Il primo avvio vero ha dati fino a LIVE_START.
    Per gli asset aggiunti dopo (ETH) il chiamante passa lost= a pending_events (marker del primo avvio nello stato)."""
    return prev is None and pd.Timestamp(cur["date"]) > pd.Timestamp(ASSET_LIVE_START.get(asset_of(cur), LIVE_START))


def _restore_state(cur: dict, st: dict) -> None:
    """Stato perso: ricostruisce dalla simulazione cosa l'utente conosceva già. Le posizioni dello storico contano come
    annunciate; ingressi e uscite degli ultimi RECENT_DAYS restano da comunicare (passi 2 e 5), quelli più vecchi si
    registrano senza messaggio. La posizione in corso conta come annunciata: il messaggio di ripristino ne dà i livelli."""
    for t in cur.get("history", {}).get("trades", []):
        s = t["signal"]
        for fld in ("notified",) + (() if _recent(t["entry"], cur["date"]) else ("entered",)) + \
                (("exit_announced",) if t["reason"] != "open" else ()):
            if s not in st[fld]:
                st[fld].append(s)
    for fld in ("notified", "entered", "exit_announced"):
        st[fld] = st[fld][-30:]
    k = _pos_key(cur)
    if cur["status"] in ("aperto", "uscita"):
        st.update(trail_notified=cur.get("trail"), trail_sig=k, side=cur.get("side"))
    st["restore_pending"] = True


def pending_events(cur: dict, prev: dict | None, lost: bool | None = None) -> tuple[list[dict], dict]:
    """(eventi da inviare, stato di base). Lo stato di base NON contiene le marcature degli eventi: si aggiungono
    con apply_marks solo dopo un invio riuscito. prev=None = primo avvio dal vivo: la posizione già aperta si mostra
    come "in corso" con un solo messaggio informativo, senza rimandarla come segnale nuovo. prev=None con dati
    successivi a LIVE_START = stato perso (state_lost): avviso di ripristino con l'ultima situazione W3, senza perdere
    ingressi e uscite degli ultimi giorni (ricostruiti dalla simulazione)."""
    ev, k, status = [], _pos_key(cur), cur["status"]
    trades = cur.get("history", {}).get("trades", [])
    by_sig = {t["signal"]: t for t in trades}
    lost = state_lost(cur, prev) if lost is None else (prev is None and lost)
    first = prev is None and not lost
    st = _norm_state(prev or {})
    if lost:
        _restore_state(cur, st)
    if st.get("restore_pending"):   # resta in sospeso finché Telegram non conferma l'avviso
        last = next((t for t in reversed(trades) if t["reason"] != "open"), None)
        ev.append({"type": "w_restore", "w": cur, "last": last, "mark": [("set", "restore_pending", False)]})
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


def diff_events(cur: dict, prev: dict | None, lost: bool | None = None) -> tuple[list[dict], dict]:
    """(eventi nuovi, stato con tutti gli eventi marcati come inviati). Per l'invio reale usare send_events,
    che marca solo gli eventi confermati da Telegram."""
    ev, st = pending_events(cur, prev, lost)
    for e in ev:
        apply_marks(st, e)
    return ev, st


def send_events(cur: dict, prev: dict | None, send, lost: bool | None = None) -> tuple[list[dict], dict]:
    """Invia gli eventi uno per uno (send(text) -> message_id/True se riuscito, False/None se no) e marca nello
    stato solo quelli riusciti. Restituisce (eventi inviati, stato da salvare). Un errore di formattazione o di
    rete su un evento non blocca gli altri."""
    ev, st = pending_events(cur, prev, lost)
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


# ---------------------------------------------------------------- testi Telegram (formato in radar/telegram.py)

def _reason_txt(r: str | None, side: str | None) -> str:
    return tg._reason(r, side)


def _exit_rules(side: str, trail_dist: float | None = None, ema21: float | None = None) -> str:
    L = side == "long"
    return ("<b>Come si esce</b> (alla prima delle tre): "
            + (f"uscita automatica a {tg.usd(trail_dist)} dalla miglior chiusura giornaliera, si sposta solo a tuo favore "
               "e ti avviso a ogni passo; " if trail_dist else "uscita automatica (si sposta solo a tuo favore); ")
            + f"chiusura settimanale {'sotto' if L else 'sopra'} la media a 21 settimane"
            + (f" ({tg.usd(ema21)})" if ema21 else "") + "; "
            + "distribuzione (funding medio 7 giorni "
            + ("&gt; 0,09%/giorno con flusso dei futures negativo)." if L else "&lt; −0,03%/giorno con flusso dei futures positivo)."))


def _mkt(market: str, expo: float) -> str:
    base = (f"spot, esposizione {tg.num(expo)}x, niente leva né funding" if market == "spot"
            else f"perp, margine isolato, esposizione {tg.num(expo)}x del capitale")
    return f"<b>Mercato</b>: {base}."


def _qty(x: dict) -> str:
    """Quantità dell'asset (chiave "qty"; "btc" nei report salvati prima di ETH)."""
    q = x.get("qty", x.get("btc"))
    return "n.d." if q is None else tg.num(q, 4)


def _amount(x: dict, a: str) -> str:
    return f"Importo: {tg.usd(x['notional'])} = {_qty(x)} {a} su {tg.usd(x['capital'])}"


def exit_at(w: dict | None, x: float) -> tuple[float, float] | None:
    """Esito (% sul capitale, dollari) se si esce al prezzo x: stessa formula di exits_block (w["uscite"]["calc"])."""
    u = (w or {}).get("uscite") or {}
    c, ep = u.get("calc"), u.get("entry_px")
    if not c or not ep:
        return None
    xs = x * (1 - c["slip"] * c["sg"])
    r = c["pnl_pct"] / 100 + c["sg"] * c["expo"] * (xs - c["px0"]) / ep - c["expo"] * xs / ep * c["fee"]
    return round(r * 100, 2), round(c["capital"] * r, 0)


def _if_hit(w: dict, label: str = "Se scatta", icon: bool = True) -> str | None:
    """Esito se scatta ora l'uscita automatica (w["uscite"]["trail"], lo stesso dato della dashboard)."""
    t = ((w.get("uscite") or {}).get("trail")) or {}
    if t.get("usd") is None or t.get("pct_cap") is None:
        return None
    ic = ("🎯 " if t["usd"] > 0 else "🛑 ") if icon else ""
    return f"{ic}{label}: {tg.money(t['pct_cap'], t['usd'])}"


def _state_plain(w: dict | None) -> str:
    if not w:
        return "non calcolato"
    s = w.get("status")
    if s == "aperto":
        return f"{w['side']} aperto, uscita automatica {tg.usd(w['trail'])}"
    if s == "uscita":
        return f"{w['side']}, chiusura lunedì all'apertura"
    if s == "segnale":
        return f"segnale {w['side']}, entrata lunedì all'apertura"
    return "nessuna posizione"


def format_event(ev: dict) -> str:
    t, w = ev["type"], ev["w"]
    a = asset_of(w)
    side = ev.get("side") or w.get("side") or ev.get("trade", {}).get("side", "")
    S, ic, L = tg.side_up(side), tg.ICON.get(side, "⚪"), side == "long"
    H, M, foot = tg.head, tg.msg, tg.foot()
    usd, dm, gdm, pc = tg.usd, tg.dm, tg.gdm, tg.pc

    if t == "w_signal" and w["status"] == "segnale":
        p = w["plan"]
        return M(
            H(ic, a, f"Nuovo {S}: entra lunedì all'apertura"),
            f"Entrata: ~<b>{usd(p['entry_est'])}</b> a mercato, {gdm(pd.Timestamp(w['signal_date']) + pd.Timedelta(days=1))}",
            _amount(p, a),
            f"🛑 Uscita in perdita: {usd(p['stop'])} (circa −{usd(p['loss_usd'])})",
            "🎯 Profitto: l'uscita segue il prezzo",
            "Lunedì ti confermo il prezzo eseguito.",
            tg.details(f"<b>Stop iniziale</b> {usd(p['stop'])} = {'−' if L else '+'}{tg.num(p['stop_pct'], 1)}% dal prezzo; "
                       f"perdita stimata allo stop ~{usd(p['loss_usd'])} (costi inclusi).",
                       f"<b>Perché</b>: chiusura settimanale del {dm(w['signal_date'])} a {usd(w['price'])}, tendenza "
                       f"{'rialzista' if L else 'ribassista'}, flusso dei futures {tg.sig(w['flow'])}.",
                       _mkt(p["market"], p["expo"]),
                       _exit_rules(side, p.get("trail_dist"), p.get("ema21")),
                       "Uscita automatica = 2,5 volte la volatilità media settimanale (ATR) dalla miglior chiusura.",
                       W3_TEXTS.get(a, W3_TEXT)),
            foot)

    if t == "w_signal":   # posizione aperta mai annunciata (giri saltati durante il segnale)
        return M(
            H(ic, a, f"{S} già aperto dal {dm(w['entry'])} (segnale in ritardo)"),
            f"Entrata {gdm(w['entry'])} a <b>{usd(w['entry_px'])}</b> · ora {usd(w['price'])}",
            f"Risultato: {tg.money_cap(w['capital'], w['pnl_pct'])}",
            f"🛑 Uscita automatica: <b>{usd(w['trail'])}</b>",
            f"Media a 21 settimane: {usd(w['ema21'])}",
            tg.details(f"Segnale del {dm(w['signal_date'])}: i giri precedenti non l'avevano comunicato. "
                       "Se entri ora, entri a un prezzo diverso.", _mkt(w["market"], w["expo"]), _exit_rules(side)),
            foot)

    if t == "w_entry":
        x = ev["trade"]
        if w.get("status") in ("aperto", "uscita") and w.get("signal_date") == x["signal"]:
            return M(
                H(ic, a, f"{S} aperto a {usd(x['entry_px'])}"),
                f"Entrata {gdm(x['entry'])} all'apertura (segnale del {dm(x['signal'])})",
                _amount(w, a),
                f"Prezzo ora: {usd(w['price'])} · {tg.money_cap(w['capital'], w['pnl_pct'])}",
                f"🛑 Uscita automatica: <b>{usd(w['trail'])}</b>",
                tg.details(f"Stop iniziale {usd(w['stop0'])}. {_mkt(x['market'], x['expo'])}"),
                foot)
        if x.get("reason") == "open" or x.get("exit_px") is None:
            return M(H(ic, a, f"{S} aperto a {usd(x['entry_px'])}"),
                     f"Entrata {gdm(x['entry'])} all'apertura (segnale del {dm(x['signal'])})",
                     tg.details(_mkt(x["market"], x["expo"])), foot)
        win = (x.get("pnl_pct") or 0) > 0
        return M(
            H("🎯" if win else "🛑", a, f"{S} aperto e già chiuso: {pc(x['pnl_pct'])}"),
            f"Entrata {gdm(x['entry'])} a {usd(x['entry_px'])} (segnale del {dm(x['signal'])})",
            f"Uscita {gdm(x['exit'])} a {usd(x['exit_px'])} · {tg.esc(_reason_txt(x['reason'], side))}",
            foot)

    if t == "w_info":
        return M(
            H(ic, a, f"{S} in corso dal {dm(w['entry'])}: non è un segnale nuovo"),
            f"Da oggi il radar segue anche {a}.",
            f"Entrata {gdm(w['entry'])} a <b>{usd(w['entry_px'])}</b> · ora {usd(w['price'])}",
            f"Risultato: {tg.money_cap(w['capital'], w['pnl_pct'])} · {pc(w['move_pct'])} sul prezzo",
            _amount(w, a),
            f"🛑 Uscita automatica: <b>{usd(w['trail'])}</b>",
            f"Media a 21 settimane: {usd(w['ema21'])}",
            tg.details("Se decidi di seguirla ora, entri a un prezzo diverso.", _mkt(w["market"], w["expo"]), _exit_rules(side)),
            foot)

    if t == "w_trail":
        return M(
            H("🔔", a, f"Uscita automatica {'alzata' if L else 'abbassata'} a {usd(w['trail'])}"),
            f"Era {usd(ev['old'])} · si sposta solo a tuo favore",
            f"{S} da {usd(w['entry_px'])} · ora {usd(w['price'])} · {tg.money_cap(w['capital'], w['pnl_pct'])}",
            _if_hit(w),
            foot)

    if t == "w_dist":
        return M(
            H("⏳", a, f"Possibile uscita {tg.art(side, 'da')}: decide domenica"),
            "Se la settimana chiudesse oggi si uscirebbe lunedì per distribuzione.",
            f"Funding medio 7g {pc(w['fund7'] * 100, 4)}/giorno · flusso futures {tg.sig(w['flow'])}",
            f"<b>Nessuna azione ora</b>: decide la chiusura di {gdm(next_decision(w['date']))} (UTC).",
            f"🛑 Uscita automatica: {usd(w['trail'])}",
            tg.details("Distribuzione = funding e flusso dei futures contrari alla posizione: "
                       + ("funding medio 7g sopra 0,09%/giorno con flusso negativo." if L
                          else "funding medio 7g sotto −0,03%/giorno con flusso positivo.")),
            foot)

    if t == "w_restore":
        x = ev.get("last")
        pos = None
        if w.get("status") in ("aperto", "uscita"):
            pos = (f"{tg.ICON.get(w['side'], '⚪')} {tg.side_up(w['side'])} dal {dm(w['entry'])} a {usd(w['entry_px'])} · "
                   f"{tg.money_cap(w['capital'], w['pnl_pct'])}")
        return M(
            H("⚠️", a, "Avvisi ripristinati: nessuna azione"),
            "Lo stato degli avvisi mancava: ricostruito dalla simulazione.",
            pos or f"Situazione: {_state_plain(w)}",
            f"🛑 Uscita automatica: {usd(w['trail'])} · media 21 sett. {usd(w['ema21'])}" if pos else None,
            tg.details((f"Ultima chiusa: {x['side']} dal {dm(x['entry'])} a {usd(x['entry_px'])}, uscita {dm(x['exit'])} a "
                        f"{usd(x['exit_px'])} ({tg.esc(_reason_txt(x['reason'], x['side']))}), {pc(x['pnl_pct'])} sul capitale."
                        if x else None),
                       f"Dati fino al {dm(w['date'])}. Ingressi e uscite degli ultimi {RECENT_DAYS} giorni seguono in "
                       "messaggi separati."),
            foot)

    if t == "w_exit_next":
        est = w["pnl_pct"]
        return M(
            H("🎯" if est > 0 else "🛑", a, f"Chiudi {tg.art(side)} lunedì all'apertura"),
            f"Motivo: {tg.esc(_reason_txt(w['reason'], side))} ({gdm(w['exit_date'])})",
            f"Entrata {dm(w['entry'])} a {usd(w['entry_px'])} · ora {usd(w['price'])}",
            f"Risultato stimato: {tg.money_cap(w['capital'], est)}",
            "Lunedì ti confermo prezzo eseguito e risultato.",
            foot)

    if t == "w_exit":
        x = ev["trade"]
        win = x["pnl_pct"] > 0
        cap = w.get("capital") or 0
        return M(
            H("🎯" if win else "🛑", a, f"{S} chiuso in {'profitto' if win else 'perdita'}: {pc(x['pnl_pct'])}"),
            f"Uscita {gdm(x['exit'])} a <b>{usd(x['exit_px'])}</b> · {tg.esc(_reason_txt(x['reason'], side))}",
            f"Entrata {gdm(x['entry'])} a {usd(x['entry_px'])} · {pc(x['move_pct'])} sul prezzo",
            f"Risultato: {tg.money_cap(cap, x['pnl_pct'])} del capitale" if cap
            else f"Risultato: <b>{pc(x['pnl_pct'])}</b> del capitale",
            "Ora nessuna posizione: si attende il prossimo segnale." if w.get("status") == "nessuno" else None,
            foot)

    if t == "w_retract":
        if ev["kind"] == "signal":
            return M(
                H("⚪", a, f"Segnale {S} annullato: non entrare"),
                f"Il segnale del {dm(ev['key'])} non è più valido dopo l'aggiornamento dei dati:",
                f"<i>{tg.esc(ev['why'])}</i>",
                "<b>Se sei già entrato, valuta di chiudere.</b>",
                f"Stato attuale: {_state_plain(w)}.",
                foot)
        return M(
            H(ic, a, f"Uscita annullata: tieni {tg.art(side)}"),
            "L'uscita annunciata per lunedì non è più valida:",
            f"<i>{tg.esc(ev['why'])}</i>",
            f"🛑 Uscita automatica: {usd(w['trail'])} · media 21 sett. {usd(w['ema21'])}" if w.get("trail") else None,
            foot)
    return tg.esc(str(ev))

def next_decision(today: str | pd.Timestamp) -> str:
    """Prossima decisione W3: chiusura UTC della domenica (oggi se è domenica)."""
    d = pd.Timestamp(today).normalize()
    return str((d + pd.Timedelta(days=(6 - d.dayofweek) % 7)).date())


def _state_short(a: str, c: dict | None) -> str:
    """'🔴 BTC short' / '⚪ BTC fuori' / 'BTC non calcolato' per la riga di stato del messaggio di salute."""
    if not c:
        return f"{a} non calcolato"
    if c.get("status") in ("segnale", "aperto", "uscita"):
        return f"{tg.ICON.get(c.get('side'), '⚪')} {a} {c.get('side')}"
    return f"⚪ {a} fuori"


def format_heartbeat(cur: dict | None, data_until: str, last_run: str, problems: list[str], today: str,
                     others: dict | None = None, note: str | None = None) -> str:
    """Messaggio di salute: «✅ tutto ok» (solo se il riepilogo "Oggi" è spento) o l'elenco dei problemi tecnici del giro, con
    gli avvisi sulle fonti (`note`); poi dati, ultimo giro, stato di W3.2 per asset e prossima decisione."""
    state = " · ".join([_state_short("BTC", cur)] + [_state_short(a, c) for a, c in (others or {}).items()])
    state += f" · prossima decisione {tg.gdm(next_decision(today))}"
    tail = f"Dati fino al {tg.dm(data_until)} · ultimo giro {tg.esc(last_run)}"
    if not problems:
        return tg.msg(tg.head("✅", None, "Radar attivo · tutto ok"), tail, state)
    n = len(problems)
    return tg.msg(tg.head("⚠️", None, f"Radar · {n} problem{'a' if n == 1 else 'i'} tecnic{'o' if n == 1 else 'i'}"),
                  *[f"• {tg.esc(p)}" for p in problems], note, tail, state)

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
    # "uscita": decisa alla chiusura di domenica ed eseguita all'apertura di lunedì; le ore controllate partono da lunedì
    # 00:00, cioè dopo l'uscita: nessuno stop da sorvegliare (B1, caso del 16/01/2023).
    if cur["status"] == "aperto":
        model = cur["trail"]
    elif cur["status"] == "segnale":
        model = cur["plan"]["stop"]
    else:
        return [], already
    sg = _sg(cur["side"])
    a = asset_of(cur)
    if h is None:
        from .data import ASSETS
        from .intraday import hourly_since
        h = hourly_since(pd.Timestamp(cur["date"]) + pd.Timedelta(days=1), ASSETS[a]["symbol"])
    if h is None or h.empty:
        return [], already
    if cur["status"] == "segnale" and cur["plan"].get("trail_dist") is not None:
        # come il backtest il giorno d'ingresso: stop = max(stop iniziale, apertura − 2,5 ATRw) (min per gli short)
        tl = float(h["open"].iloc[0]) - sg * float(cur["plan"]["trail_dist"])
        model = max(model, tl) if sg > 0 else min(model, tl)
    level = model if told is None else (max(model, told) if sg > 0 else min(model, told))
    hit = float(h["low"].min()) <= level if sg > 0 else float(h["high"].max()) >= level
    key = f"W:{cur['signal_date']}:{level:.0f}" if a == "BTC" else f"W:{a}:{cur['signal_date']}:{level:.0f}"
    if not hit or key in already:
        return [], already
    if told is None:
        which = "modello"
    elif abs(told - model) < 0.5:
        which = "comunicato = modello"
    else:
        which = "comunicato" if level == told else "modello"
    return ([{"level": level, "model": model, "told": told, "which": which, "side": cur["side"], "asset": a,
              "last": float(h["close"].iloc[-1]), "time": datetime.now(timezone.utc).strftime("%H:%M UTC")}],
            (list(already) + [key])[-30:])


def format_intraday(events: list[dict], w: dict | None = None) -> str:
    """Stop toccato nell'ora. `w` = stato W3.2 dell'asset (facoltativo): esito in dollari al livello toccato."""
    e = events[0]
    a = e.get("asset") or "BTC"
    why = None
    if e.get("which") == "comunicato":
        why = f"Livello = ultimo comunicato (quello del modello è {tg.usd(e['model'])})."
    elif e.get("told") is not None and e.get("which") == "modello":
        why = f"Livello = quello del modello (l'ultimo comunicato era {tg.usd(e['told'])})."
    res = exit_at(w, e["level"]) if w and asset_of(w) == a and w.get("side") == e["side"] else None
    return tg.msg(
        tg.head("🛑", a, f"Stop toccato: chiudi {tg.art(e['side'])}"),
        f"Livello <b>{tg.usd(e['level'])}</b> · prezzo ora {tg.usd(e['last'])} ({e['time']})",
        f"Risultato a questo livello: {tg.money(*res)}" if res else None,
        tg.details("Lo stop scatta al tocco. L'uscita ufficiale si registra alla chiusura giornaliera.", why),
        tg.foot())
