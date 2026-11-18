"""Parte 2 · motore di ricerca: copia di radar.weekly.simulate (W3) con agganci per le regole preregistrate.
- k: distanza in ATRw di stop iniziale e trailing (W3: 2,5).
- tp = dict(levels=(2, 3), frac=1/3): prese parziali di frac della quantità iniziale con limite a entry ± m·R (R = k·ATRw
  del segnale), riempite al livello o all'apertura se il prezzo apre oltre; il resto resta in trailing.
A agganci spenti riproduce W3 al centesimo (controllo in __main__). Non modifica radar/.

Agganci:
- allow(side, day) -> bool         filtro sugli INGRESSI W3 (decisione della domenica `day`); se False nessun ingresso
                                   quella settimana (W3 può entrare la settimana dopo se il segnale resta valido).
- expo_fn(side, wk, day) -> float  esposizione all'ingresso (predefinita: W3, tetto di rischio 25% allo stop).
- rebal_fn(side, wk, day, tr) -> float | None   esposizione obiettivo ricalcolata ogni domenica a trade aperto;
                                   eseguita all'apertura del lunedì se |obiettivo − attuale| >= REBAL_MIN.
- pyr = dict(base=..., steps=(k1, k2), adds=(a1, a2))   piramidazione: ingresso a base·E (E = esposizione W3),
                                   aggiunta di a_j·E all'apertura dopo la prima chiusura giornaliera oltre
                                   prezzo d'ingresso + side·k_j·ATRw(segnale); stop comune = trailing W3 dell'intera posizione.
Ogni evento (blocco, ribilanciamento, aggiunta) viene registrato in out["events"].
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402

REBAL_MIN = 0.10


def simulate(f: pd.DataFrame, start: str = W.START, end: str | None = None, capital: float = 10000.0, lev: float = 1.0,
             allow=None, expo_fn=None, rebal_fn=None, pyr: dict | None = None, k: float = W.STOP_K,
             tp: dict | None = None) -> dict:
    f = f[f["close"].notna()]
    if end is not None:
        f = f[f.index <= end]
    w = W.weekly_bars(f)
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    trades, events, eq = [], [], np.full(len(idx), np.nan)
    st = {}   # stato della posizione: esposizione obiettivo corrente, E piena, aggiunte fatte, ordini del giorno dopo

    def rates(expo: float) -> tuple[float, float]:
        if side < 0:
            return W.FEE_PERP, 1.0
        fs = min(expo, 1.0) / expo if expo > 0 else 1.0
        return fs * W.FEE_SPOT + (1 - fs) * W.FEE_PERP, 1 - fs

    def trade_to(target: float, px: float, i: int, why: str) -> None:
        """Porta l'esposizione a `target` (frazione dell'equity) all'apertura `px` (slippage già incluso nel px)."""
        nonlocal cash, qty, cost
        e_now = cash + qty * px - cost
        q_new = side * target * e_now / px
        dq = q_new - qty
        if abs(dq) < 1e-12:
            return
        fr, _ = rates(max(target, st["expo"]))
        if abs(q_new) < abs(qty):                       # riduzione: realizza la quota venduta
            p = 1 - q_new / qty
            cash += p * (qty * px - cost)
            cost *= (1 - p)
            qty = q_new
        else:
            cost += dq * px
            qty = q_new
        cash -= abs(dq) * px * fr
        events.append(dict(day=str(idx[i].date()), kind=why, side=side, from_expo=round(st["expo"], 3), to_expo=round(target, 3)))
        st["expo"] = target

    def close_all(px: float, i: int, reason: str) -> None:
        nonlocal cash, qty, cost, side, tr
        fr, _ = rates(st["expo"])
        cash += qty * px - cost - abs(qty) * px * fr
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1,
                  move=(px / tr["entry_px"] - 1) * side, expo_max=round(st["expo_max"], 3), adds=st.get("adds", 0),
                  tp_done=st.get("tp_done", 0))
        trades.append(tr)
        tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                full = expo_fn(side, wk, pend[3]) if expo_fn else W.exposure(side, wk["close"], wk["atr"], lev)
                lt = full * (pyr["base"] if pyr else 1.0)
                st = dict(expo=lt, full=full, expo_max=lt, adds=0, next=None)
                fr, _ = rates(lt)
                px = O[i] * (1 + W.SLIP * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * fr
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=round(px, 2), sig_close=float(wk["close"]), atr=float(wk["atr"]), expo=round(lt, 3),
                          expo_full=round(full, 3), eq0=cash + abs(q) * px * fr,
                          stop0=float(wk["close"] - side * k * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
                tr["rdist"] = k * float(wk["atr"])
                st["tp_done"], st["q0"] = 0, abs(q)
                tr["stop"] = tr["stop0"]
                events.append(dict(day=str(day.date()), kind="enter", side=side, from_expo=0.0, to_expo=round(lt, 3)))
            elif pend[0] == "rebal" and side:
                trade_to(pend[1], O[i] * (1 + W.SLIP * np.sign(pend[1] - st["expo"]) * side), i, "rebal")
                st["expo_max"] = max(st["expo_max"], st["expo"])
            pend = None
        if side and st.get("next") is not None:            # aggiunta di piramide decisa sulla chiusura di ieri
            trade_to(st["expo"] + st["next"], O[i] * (1 + W.SLIP * side), i, "add")
            st["expo_max"] = max(st["expo_max"], st["expo"])
            st["adds"] += 1
            st["next"] = None
        if side:
            tl = tr["best"] - side * k * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop
            hit = (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop)   # stesso giorno: prima lo stop (prudenza)
            while tp and not hit and st["tp_done"] < len(tp["levels"]):     # presa parziale con ordine limite a entry + m·R
                lvl = tr["entry_px"] + side * tp["levels"][st["tp_done"]] * tr["rdist"]
                if not ((side > 0 and H[i] >= lvl) or (side < 0 and L[i] <= lvl)):
                    break
                fill = (max(O[i], lvl) if side > 0 else min(O[i], lvl)) * (1 - W.SLIP * side)
                q_sell = min(tp["frac"] * st["q0"], abs(qty))
                p = q_sell / abs(qty)
                fr, _ = rates(st["expo"])
                cash += p * (qty * fill - cost) - q_sell * fill * fr
                cost *= (1 - p)
                qty *= (1 - p)
                st["expo"] *= (1 - p)
                st["tp_done"] += 1
                events.append(dict(day=str(day.date()), kind="tp", side=side, from_expo=0.0, to_expo=round(st["expo"], 3)))
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - W.SLIP * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                _, fperp = rates(st["expo"])
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
                if pyr and st["adds"] < len(pyr["steps"]):
                    kj = pyr["steps"][st["adds"]]
                    if (C[i] - tr["sig_close"]) * side >= kj * tr["atr"]:
                        st["next"] = pyr["adds"][st["adds"]] * st["full"]
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
            d = W._decide(wk, side)
            if d and d[0] == "enter" and allow is not None and not allow(d[1], day):
                events.append(dict(day=str(day.date()), kind="blocked", side=d[1], from_expo=0.0, to_expo=0.0))
                d = None
            pend = d + (wk, day) if d else None
            if pend is None and side and rebal_fn is not None:
                tgt = rebal_fn(side, wk, day, tr)
                if tgt is not None and abs(tgt - st["expo"]) >= REBAL_MIN:
                    pend = ("rebal", tgt, wk, day)
    out = {"trades": trades, "events": events, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "weekly": w,
           "open": None, "pending": None}
    if side:
        i = len(idx) - 1
        fr, _ = rates(st["expo"])
        out["open"] = dict(tr, last=float(C[i]), move=(C[i] / tr["entry_px"] - 1) * side, pnl=(eq[i] / tr["eq0"] - 1),
                           pnl_close=(eq[i] - abs(qty) * C[i] * fr) / tr["eq0"] - 1, expo_max=round(st["expo_max"], 3),
                           adds=st.get("adds", 0))
    return out


if __name__ == "__main__":
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from p2_data import load
    d = load()
    for x, s, e in ((d["f"], W.START, None), (d["fl"], "2018-01-01", "2020-12-31")):
        xx = x if e is None else x[x.index <= e]
        a, b = W.simulate(xx, start=s), simulate(x, start=s, end=e)
        print(s, "uguale a radar.weekly:", np.allclose(a["equity"].to_numpy(), b["equity"].to_numpy(), rtol=0, atol=1e-6),
              len(a["trades"]) == len(b["trades"]))
