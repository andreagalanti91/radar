"""cascata · motore di ricerca (23/11/2026). Non modifica radar/. PREREG.md (commit 9e437db).

Copia di research/tp_rientro/tp_engine.py (a sua volta copia di radar.weekly.simulate, W3.2) con uscite giornaliere (cfg):
- trig=(TL, TS): Series bool giornaliere (cascata a favore dei long / degli short, nota alla chiusura). In posizione, alla chiusura
  del giorno → uscita della quota `frac` all'apertura successiva (slippage + commissione). Mai al minimo/massimo del giorno.
- lim=k: ordine a limite a C[t−1] + lato·k·ATR14[t−1], valido nel giorno t; riempito al livello o all'apertura se apre oltre.
- force={giorni}: placebo: uscita decisa alla chiusura di quei giorni (al posto di trig/lim).
- frac: 1.0 (tutto) o 0.5 (metà, una volta per trade, nessun rientro).
- reentry: "R1" (flat → logica W3.2 alla domenica successiva), ("R2", X) (R1 + rientro all'apertura dopo la prima chiusura
  giornaliera rimbalzata di X contro il lato rispetto al prezzo d'uscita, con regime del lato valido sull'ultima settimana chiusa;
  dimensione: rischio 25% allo stop a 2,5 ATRw dalla chiusura di quel giorno), "R3" (nessun ingresso fino alla data d'uscita del
  trade W3.2 originale: cfg["windows"] = [(ingresso, uscita)] dalla simulazione base).
Ordine nel giorno: ordini all'apertura → stop/trailing → limite → funding → equity → cascata (chiusura) → decisione settimanale →
rientro R2. Lo stop nello stesso giorno prevale sul limite; l'uscita settimanale W3.2 prevale sull'uscita-cascata.
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
FAR = pd.Timestamp("2262-01-01")


def simulate(f: pd.DataFrame, cfg: dict | None = None, start: str = W.START, end: str | None = None,
             capital: float = 10000.0) -> dict:
    cfg = cfg or {}
    trig, limk, force = cfg.get("trig"), cfg.get("lim"), cfg.get("force")
    frac, rein, windows = cfg.get("frac", 1.0), cfg.get("reentry", "R1"), cfg.get("windows", [])
    rmode = rein if isinstance(rein, str) else rein[0]
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
    TL = trig[0].reindex(idx).fillna(False).to_numpy(bool) if trig else None
    TS = trig[1].reindex(idx).fillna(False).to_numpy(bool) if trig else None
    FO = idx.isin(list(force)) if force is not None else None
    if limk:
        cc = f["close"]
        trr = pd.concat([f["high"] - f["low"], (f["high"] - cc.shift()).abs(), (f["low"] - cc.shift()).abs()], axis=1).max(axis=1)
        A1 = trr.ewm(alpha=1 / 14, adjust=False).mean().shift(1).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(len(idx), np.nan)
    mem = None            # (lato, prezzo d'uscita) per R2
    block = None          # R3: nessun ingresso prima di questa data
    lastwk = None
    n_ev, evlog = 0, []

    def close_part(fr: float, px: float) -> None:
        nonlocal cash, qty, cost
        q, cst = qty * fr, cost * fr
        cash += q * px - cst - abs(q) * px * frate
        qty, cost = qty - q, cost - cst

    def close_all(px: float, i: int, reason: str) -> None:
        nonlocal cash, qty, cost, side, tr
        close_part(1.0, px)
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1,
                  move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    def casc_exit(px: float, i: int) -> None:
        nonlocal mem, block, n_ev
        n_ev += 1
        evlog.append(dict(day=str(idx[i].date()), px=round(px, 2), side=side, frac=frac))
        if frac >= 1.0:
            sd = side
            close_all(px, i, "cascata")
            mem = (sd, px)
            if rmode == "R3":
                block = FAR
                for a, b in windows:
                    if pd.Timestamp(a) <= idx[i] and (b is None or idx[i] <= pd.Timestamp(b)):
                        block = pd.Timestamp(b) if b else FAR
        else:
            close_part(frac, px)
            tr["done"] = 1

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "casc" and side:
                casc_exit(O[i] * (1 - W.SLIP * side), i)
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
                          best=O[i], curatr=float(wk["atr"]), ext=O[i], done=0, kind=pend[4])
                tr["stop"] = tr["stop0"]
                mem = None
            pend = None
        if side:
            tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop
            tr["ext"] = max(tr["ext"], H[i]) if side > 0 else min(tr["ext"], L[i])
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                if limk and FO is None and not tr["done"] and i > 0 and A1[i] == A1[i]:
                    lvl = C[i - 1] + side * limk * A1[i]
                    if (side > 0 and H[i] >= lvl) or (side < 0 and L[i] <= lvl):
                        casc_exit((max(O[i], lvl) if side > 0 else min(O[i], lvl)) * (1 - W.SLIP * side), i)
                if side:
                    cash -= fperp * qty * C[i] * FU[i]
                    tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if side and not tr["done"]:
            hit = FO[i] if FO is not None else (TL is not None and (TL[i] if side > 0 else TS[i]))
            if hit:
                pend = ("casc",)
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            lastwk = wk
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            if not side and block is not None:
                if day < block:
                    d = None
                else:
                    block = None
            if d:
                pend = d + (wk, day, "segnale")
            if mem is not None and not side and not (wk["reg_long"] if mem[0] > 0 else wk["reg_short"]):
                mem = None
        if rmode == "R2" and not side and pend is None and mem is not None and lastwk is not None:
            sd, xp = mem
            if (lastwk["reg_long"] if sd > 0 else lastwk["reg_short"]) and (C[i] / xp - 1) * sd <= -rein[1]:
                pend = ("enter", sd, {"close": C[i], "atr": float(lastwk["atr"])}, day, "rientroR2")
    out = {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "weekly": w, "open": None, "n_ev": n_ev,
           "evlog": evlog}
    if side:
        i = len(idx) - 1
        out["open"] = dict(tr, last=float(C[i]), move=(C[i] / tr["entry_px"] - 1) * side, pnl=(eq[i] / tr["eq0"] - 1),
                           pnl_close=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1)
    return out
