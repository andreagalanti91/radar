"""Copia di research/tp_rientro/tp_engine.py per tradera_test (WV2): unica modifica, cfg["tp_fn"](i, lato, prezzo d'ingresso)
restituisce la distanza del TP in frazione (o None) al posto di una percentuale fissa. Non modifica radar/.

TP e rientro su W3.2 · motore di ricerca (22/11/2026).

Copia di radar.weekly.simulate (W3.2, rischio allo stop 25%) con tre aggiunte facoltative (cfg):
- tp=(p, frac): take profit con limite a prezzo d'ingresso × (1 ± p); controllo giornaliero su massimo/minimo; riempito al livello
  o all'apertura se il prezzo apre oltre, con slippage e commissione; frac = 1 (tutto) o 0,5 (metà della quantità iniziale,
  il resto segue le regole W3.2). Il giorno in cui si tocca lo stop vale lo stop (nessun TP).
- reentry=("A",) dopo un TP totale si torna flat e vale la logica W3.2 (ingresso alla decisione settimanale se il segnale è vero);
  reentry=("B", X): come A, più rientro nello stesso lato alla decisione settimanale se il regime di quel lato è ancora valido
  (long: chiusura > SMA40 e EMA20 in salita; short: chiusura < SMA40, SMA40 in calo su 4 sett., EMA20 in calo) e la chiusura
  settimanale è entro ±X dal prezzo di uscita del TP. La memoria del TP si cancella al primo nuovo ingresso o a regime finito.
- trail2=(act, k2): quando la miglior chiusura è oltre act dal prezzo d'ingresso il trailing passa da 2,5 a k2 ATRw (a cricchetto).
- tp_rng: generatore numpy per il placebo: a ogni ingresso il livello del TP si estrae uniforme in [0,05; 0,30].
Ogni trade registra anche il MFE (massimo/minimo intragiornaliero dall'ingresso all'uscita) e la miglior chiusura.
Ordine nel giorno: ordini all'apertura → stop/trailing → TP → funding → equity → decisione settimanale.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402

assert W.R_LONG == W.R_SHORT == 0.25 and W.STOP_K == W.TRAIL_K == 2.5


def simulate(f: pd.DataFrame, cfg: dict | None = None, start: str = W.START, end: str | None = None,
             capital: float = 10000.0) -> dict:
    cfg = cfg or {}
    tp, rein, trail2, rng = cfg.get("tp"), cfg.get("reentry", ("A",)), cfg.get("trail2"), cfg.get("tp_rng")
    f = f[f["close"].notna()]
    if end:
        f = f[f.index <= end]
    w = W.weekly_bars(f)
    c = w["close"]
    w["reg_long"] = ((c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))).fillna(False)
    w["reg_short"] = ((c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))).fillna(False)
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)
    tpmem = None   # (lato, prezzo di uscita del TP) per il rientro B
    n_tp = 0

    def close_part(frac: float, px: float) -> None:
        nonlocal cash, qty, cost
        q, cst = qty * frac, cost * frac
        cash += q * px - cst - abs(q) * px * frate
        qty, cost = qty - q, cost - cst

    def close_all(px: float, i: int, reason: str) -> None:
        nonlocal cash, qty, cost, side, tr
        close_part(1.0, px)
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1,
                  move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = W.exposure(side, wk["close"], wk["atr"])
                fs = min(lt, 1.0) / lt if side > 0 else 0.0
                frate, fperp = fs * W.FEE_SPOT + (1 - fs) * W.FEE_PERP, 1 - fs
                px = O[i] * (1 + W.SLIP * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=round(px, 2), sig_close=float(wk["close"]), atr=float(wk["atr"]), expo=round(lt, 3),
                          eq0=cash + abs(q) * px * frate, stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]),
                          best=O[i], curatr=float(wk["atr"]), ext=O[i], tp_done=0, kind=pend[4],
                          tp_p=(cfg["tp_fn"](i, side, px) if cfg.get("tp_fn") else (float(rng.uniform(0.05, 0.30)) if rng is not None else (tp[0] if tp else None))))
                tr["stop"] = tr["stop0"]
                tpmem = None
            pend = None
        if side:
            k = W.TRAIL_K
            if trail2 and (tr["best"] / tr["entry_px"] - 1) * side >= trail2[0]:
                k = trail2[1]
            tl = tr["best"] - side * k * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop
            tr["ext"] = max(tr["ext"], H[i]) if side > 0 else min(tr["ext"], L[i])
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else ("trail2" if k != W.TRAIL_K else "trail"))
            else:
                if tr["tp_p"] is not None and not tr["tp_done"]:
                    lvl = tr["entry_px"] * (1 + side * tr["tp_p"])
                    if (side > 0 and H[i] >= lvl) or (side < 0 and L[i] <= lvl):
                        fillp = (max(O[i], lvl) if side > 0 else min(O[i], lvl)) * (1 - W.SLIP * side)
                        tr["tp_done"], tr["tp_day"] = 1, str(day.date())
                        n_tp += 1
                        frac = tp[1] if tp else 1.0
                        if frac >= 1.0:
                            sd = side
                            close_all(fillp, i, "tp")
                            tpmem = (sd, fillp)
                        else:
                            close_part(frac, fillp)
                if side:
                    cash -= fperp * qty * C[i] * FU[i]
                    tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            kind = "segnale"
            if d is None and not side and tpmem is not None and rein[0] == "B":
                sd, xp = tpmem
                if not (wk["reg_long"] if sd > 0 else wk["reg_short"]):
                    tpmem = None
                elif abs(wk["close"] / xp - 1) <= rein[1]:
                    d, kind = ("enter", sd), "rientroB"
            elif tpmem is not None and not side and not (wk["reg_long"] if tpmem[0] > 0 else wk["reg_short"]):
                tpmem = None
            pend = d + (wk, day, kind) if d else None
    out = {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "weekly": w, "open": None, "n_tp": n_tp}
    if side:
        i = len(idx) - 1
        out["open"] = dict(tr, last=float(C[i]), move=(C[i] / tr["entry_px"] - 1) * side, pnl=(eq[i] / tr["eq0"] - 1),
                           pnl_close=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1)
    return out
