"""forza_giornaliera · motore di ricerca (23/11/2026). Non modifica radar/. PREREG.md (commit 32bcbba).

Copia di radar.weekly.simulate (W3.2) con due aggiunte facoltative (cfg):
- ein: ingresso ritardato dopo il segnale domenicale (giorno 0).
    {"agree": (AL, AS), "K": k}   AL/AS array bool giornalieri (flusso concorde con long/short alla chiusura). Si entra
                                   all'apertura dopo il primo giorno 0..k−1 concorde; se nessuno, all'apertura del giorno k+1.
                                   Dato mancante (NaN → array "nd" vero) = regola inattiva, ingresso come W3.2.
    {"delays": [..]}               placebo: ritardo fisso per ogni ingresso in ordine (0 = come W3.2).
    {"level": (SUP, RES), "K": 5}  limite sul livello (array giornalieri noti alla chiusura del giorno 0; NaN = nessun livello →
                                   come W3.2), valido nei giorni 1..K, eseguito al livello o all'apertura se apre oltre, senza
                                   slippage; non eseguito → mercato all'apertura del giorno K+1.
- eout: uscita anticipata e rientro.
    {"trig": (TL, TS), "frac": 1.0}  TL/TS array bool: alla chiusura del giorno, con posizione piena, uscita della quota frac
                                   all'apertura successiva. Rientro all'apertura del lunedì dopo la prima decisione domenicale
                                   successiva all'uscita in cui il trade è ancora aperto e W3.2 non esce.
    {"force": {data: n}, ...}      placebo: per ogni trade (data del segnale) n uscite in giorni casuali (rng) del trade.
Un trade = un segnale W3.2; l'esposizione, lo stop iniziale e il trailing sono quelli di W3.2 (calcolati sulla settimana del
segnale; il trailing parte dall'ingresso effettivo). Ordine nel giorno: ordini all'apertura → limite d'ingresso → stop/trailing →
funding → equity → trigger giornaliero → decisione settimanale.
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
    ein, eout = cfg.get("ein"), cfg.get("eout")
    f = f[f["close"].notna()]
    if end:
        f = f[f.index <= end]
    w = W.weekly_bars(f)
    idx = f.index
    n = len(idx)
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = W.FEE_PERP, 1.0
    trades, eq = [], np.full(n, np.nan)
    wait = None          # ingresso in attesa: dict(side, wk, day, i0, limit)
    early = None         # quota da chiudere all'apertura successiva
    reenter = False      # rientro all'apertura successiva
    n_in = 0
    log = []             # (segnale, tipo, data, prezzo)
    delays = list(ein["delays"]) if ein and "delays" in ein else None
    forced: set = set()

    def close_part(frac: float, px: float) -> None:
        nonlocal cash, qty, cost
        q, cst = qty * frac, cost * frac
        cash += q * px - cst - abs(q) * px * frate
        qty, cost = qty - q, cost - cst

    def close_all(px: float, i: int, reason: str) -> None:
        nonlocal cash, qty, cost, side, tr, early, reenter
        if qty:
            close_part(1.0, px)
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1,
                  move=(px / tr["entry_px"] - 1) * side)
        trades.append(tr)
        tr, qty, cost, side, early, reenter = None, 0.0, 0.0, 0, None, False

    def enter(sd: int, wk, sigday, i: int, px: float, delay: int, lim: bool = False) -> None:
        nonlocal cash, qty, cost, side, tr, frate, fperp, n_in
        side = sd
        lt = W.exposure(side, wk["close"], wk["atr"])
        fs = min(lt, 1.0) / lt if side > 0 else 0.0
        frate, fperp = fs * W.FEE_SPOT + (1 - fs) * W.FEE_PERP, 1 - fs
        q = side * lt * cash / px
        qty, cost = q, q * px
        cash -= abs(q) * px * frate
        tr = dict(signal=str(sigday.date()), entry=str(idx[i].date()), side="long" if side > 0 else "short",
                  entry_px=round(px, 2), sig_close=float(wk["close"]), atr=float(wk["atr"]), expo=lt,
                  eq0=cash + abs(q) * px * frate, stop0=float(wk["close"] - side * W.STOP_K * wk["atr"]),
                  best=(px if lim else O[i]), curatr=float(wk["atr"]), delay=delay, n_early=0, out=0.0, i_entry=i)
        tr["stop"] = tr["stop0"]
        n_in += 1

    for i in range(t0, n):
        day = idx[i]
        # --- ordini all'apertura
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                enter(pend[1], pend[2], pend[3], i, O[i] * (1 + W.SLIP * pend[1]), pend[4])
            pend = None
        if side and early:
            px = O[i] * (1 - W.SLIP * side)
            close_part(early, px)
            tr["out"], tr["n_early"] = early, tr["n_early"] + 1
            log.append((tr["signal"], "uscita", str(day.date()), round(px, 2)))
            early = None
        elif side and reenter and tr["out"] > 0:
            px = O[i] * (1 + W.SLIP * side)
            eqn = cash + qty * px - cost
            dq = side * tr["expo"] * eqn / px - qty
            if dq * side > 0:
                qty, cost = qty + dq, cost + dq * px
                cash -= abs(dq) * px * frate
            tr["out"] = 0.0
            log.append((tr["signal"], "rientro", str(day.date()), round(px, 2)))
        reenter = False
        # --- ingresso a limite in attesa
        if wait is not None and not side and wait.get("limit") is not None and i > wait["i0"]:
            sd, lv = wait["side"], wait["limit"]
            if (sd > 0 and L[i] <= lv) or (sd < 0 and H[i] >= lv):
                px = min(O[i], lv) if sd > 0 else max(O[i], lv)
                enter(sd, wait["wk"], wait["day"], i, px, i - wait["i0"] - 1, lim=True)
                tr["limit"] = True
                wait = None
        # --- stop / trailing
        if side:
            tl = tr["best"] - side * W.TRAIL_K * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        # --- trigger giornaliero di uscita anticipata (alla chiusura)
        if side and eout and tr["out"] == 0 and early is None:
            if "trig" in eout:
                if (eout["trig"][0] if side > 0 else eout["trig"][1])[i]:
                    early = eout.get("frac", 1.0)
            elif "force" in eout and (tr["signal"], i) in forced:
                early = eout.get("frac", 1.0)
        # --- attesa dell'ingresso (giorni dopo la domenica)
        if wait is not None and not side and pend is None and i > wait["i0"]:
            j = i - wait["i0"]
            if wait.get("limit") is not None:
                if j >= wait["K"]:
                    pend = ("enter", wait["side"], wait["wk"], wait["day"], j)
                    wait = None
            elif wait.get("delay") is not None:
                if j >= wait["delay"]:
                    pend = ("enter", wait["side"], wait["wk"], wait["day"], j)
                    wait = None
            else:
                ok = (ein["agree"][0] if wait["side"] > 0 else ein["agree"][1])[i]
                if (j <= wait["K"] - 1 and ok) or j >= wait["K"]:
                    pend = ("enter", wait["side"], wait["wk"], wait["day"], j)
                    wait = None
        # --- decisione settimanale
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            if d and d[0] == "exit":
                pend = d + (wk, day)
            elif d and d[0] == "enter":
                sd = d[1]
                if not ein:
                    pend = ("enter", sd, wk, day, 0)
                elif delays is not None:
                    dl = delays.pop(0) if delays else 0
                    if dl <= 0:
                        pend = ("enter", sd, wk, day, 0)
                    else:
                        wait = dict(side=sd, wk=wk, day=day, i0=i, delay=dl)
                elif "level" in ein:
                    lv = (ein["level"][0] if sd > 0 else ein["level"][1])[i]
                    if np.isfinite(lv):
                        wait = dict(side=sd, wk=wk, day=day, i0=i, limit=float(lv), K=ein["K"])
                    else:
                        pend = ("enter", sd, wk, day, 0)
                else:
                    ok = (ein["agree"][0] if sd > 0 else ein["agree"][1])[i]
                    nd = ein["nd"][i] if "nd" in ein else False
                    if ok or nd:
                        pend = ("enter", sd, wk, day, 0)
                    else:
                        wait = dict(side=sd, wk=wk, day=day, i0=i, K=ein["K"])
            elif side and tr["out"] > 0:
                reenter = True
        # --- placebo delle uscite: estrazione dei giorni alla prima chiusura del trade
        if side and eout and "force" in eout and not tr.get("_drawn"):
            tr["_drawn"] = True
            k = eout["force"].get(tr["signal"], 0)
            span = eout["span"].get(tr["signal"])
            if k and span and span[1] > span[0]:
                for x in eout["rng"].choice(np.arange(span[0], span[1]), size=min(k, span[1] - span[0]), replace=False):
                    forced.add((tr["signal"], int(x)))
    out = {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "weekly": w, "open": None, "log": log,
           "wait": wait, "pend": pend}
    if side:
        i = n - 1
        out["open"] = dict(tr, last=float(C[i]), move=(C[i] / tr["entry_px"] - 1) * side, pnl=(eq[i] / tr["eq0"] - 1),
                           pnl_close=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1)
    return out
