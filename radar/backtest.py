"""Backtest giornaliero con DCA in entrata/uscita, commissioni e funding.

Convenzioni conservative con barre giornaliere:
- il segnale si calcola sulla chiusura di t, il primo ingresso è all'open di t+1
- nella stessa giornata i limit DCA si riempiono prima di controllare lo stop
- se nello stesso giorno si toccano stop e take profit si assume lo stop
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .strategy import Params, compute_signals

FEES = {"spot": 0.001, "futures": 0.0005}  # per lato (taker)


def run(f: pd.DataFrame, p: Params, market: str = "futures", start=None, end=None, signals: pd.DataFrame | None = None) -> pd.DataFrame:
    s = compute_signals(f, p) if signals is None else signals
    if start:
        s = s[s.index >= pd.Timestamp(start)]
    if end:
        s = s[s.index < pd.Timestamp(end)]
    fee = FEES[market]
    idx, o, h, l, c = s.index, s["open"].values, s["high"].values, s["low"].values, s["close"].values
    atr, fund = s["atr"].values, s["funding"].fillna(0).values
    longs, shorts = s["long_sig"].values, s["short_sig"].values
    setup = s["setup"].values if "setup" in s else np.array([""] * len(s))
    trades, i, n = [], 0, len(s)
    while i < n - 1:
        side = "long" if longs[i] else "short" if (shorts[i] and market == "futures") else None
        if not side:
            i += 1
            continue
        sg = 1 if side == "long" else -1
        a = atr[i]
        e0 = o[i + 1]
        levels = [e0 - sg * k * p.entry_step_atr * a for k in range(len(p.entry_weights))]
        filled = [False] * len(levels)
        qty = cost = 0.0
        stop = e0 - sg * p.stop_atr * a
        tps = list(p.tp_atr)
        tp_w = list(p.tp_weights)
        tp_hit = 0
        realized = fees = funding = 0.0
        best = e0
        pos = 0.0  # quantità aperta (in unità di capitale / prezzo)
        exit_reason, j = None, i + 1
        D = lambda k: str(idx[k].date())
        # registro operativo del trade: segnale, piano, ogni ingresso e ogni uscita
        ev = [{"date": D(i), "type": "signal", "price": round(float(c[i]), 1),
               "note": f"segnale {setup[i]} alla chiusura"}]
        plan = {"entries": [round(float(lv), 1) for lv in levels], "weights": list(p.entry_weights),
                "stop": round(float(stop), 1), "atr": round(float(a), 1),
                "tp_atr": list(p.tp_atr), "tp_weights": list(p.tp_weights), "trail_atr": p.trail_atr}
        for j in range(i + 1, min(n, i + 1 + p.max_hold)):
            # 1) ingressi DCA
            for k, lv in enumerate(levels):
                if filled[k] or (k > 0 and j - (i + 1) >= p.entry_window) or tp_hit:
                    continue
                hit = (k == 0) or (sg == 1 and l[j] <= lv) or (sg == -1 and h[j] >= lv)
                if hit:
                    px = e0 if k == 0 else (min(lv, o[j]) if sg == 1 else max(lv, o[j]))
                    q = p.entry_weights[k] / px
                    filled[k] = True
                    ev.append({"date": D(j), "type": "entry", "price": round(float(px), 1), "pct": round(p.entry_weights[k] * 100),
                               "note": "ingresso all'apertura" if k == 0 else f"limit DCA {k + 1} eseguito"})
                    qty += q
                    pos += q
                    cost += q * px
                    fees += q * px * fee
            avg = cost / qty
            # 2) stop
            if (sg == 1 and l[j] <= stop) or (sg == -1 and h[j] >= stop):
                px = min(stop, o[j]) if sg == 1 else max(stop, o[j])
                realized += sg * pos * (px - avg)
                fees += pos * px * fee
                exit_reason = "stop" if tp_hit == 0 else ("stop_be" if abs(px - avg) / avg < 0.003 else "trail")
                ev.append({"date": D(j), "type": "exit", "kind": exit_reason, "price": round(float(px), 1),
                           "pct": round(pos / qty * 100), "note": {"stop": "stop loss", "stop_be": "stop a pareggio",
                                                                  "trail": "trailing stop"}[exit_reason]})
                pos = 0
                break
            # 3) take profit a scaglioni
            while tp_hit < len(tps):
                tp = avg + sg * tps[tp_hit] * a
                if (sg == 1 and h[j] >= tp) or (sg == -1 and l[j] <= tp):
                    q = min(pos, qty * tp_w[tp_hit])
                    realized += sg * q * (tp - avg)
                    fees += q * tp * fee
                    ev.append({"date": D(j), "type": "exit", "kind": f"tp{tp_hit + 1}", "price": round(float(tp), 1),
                               "pct": round(q / qty * 100), "note": f"take profit {tp_hit + 1} (+{tps[tp_hit]} ATR dal medio)"})
                    pos -= q
                    tp_hit += 1
                    if tp_hit == 1:  # stop a pareggio (con commissioni)
                        stop = avg * (1 + sg * 2 * fee)
                else:
                    break
            # 4) trailing sul residuo dopo TP1
            best = max(best, c[j]) if sg == 1 else min(best, c[j])
            if tp_hit >= 1:
                trail = best - sg * p.trail_atr * a
                stop = max(stop, trail) if sg == 1 else min(stop, trail)
            if market == "futures":
                funding -= sg * pos * c[j] * fund[j]
            if pos <= 1e-12:
                exit_reason = "tp"
                break
        still_open = pos > 1e-12 and j == n - 1 and (j - i) < p.max_hold
        if still_open:
            pnl = realized - fees + funding + sg * pos * (c[j] - avg)
            trades.append({
                "signal_date": idx[i].date(), "exit_date": None, "side": side, "setup": setup[i],
                "days": j - i, "tranches": sum(filled), "avg_entry": round(avg, 1),
                "invested": round(cost, 3), "tp_hit": tp_hit, "exit": "open",
                "pnl_pct_invested": pnl / cost * 100, "pnl_pct_capital": pnl * 100,
                "stop": round(stop, 1), "remaining": round(pos / qty, 3),
                "pending_entries": [round(lv, 1) for k, lv in enumerate(levels)
                                    if not filled[k] and not tp_hit and j - (i + 1) < p.entry_window],
                "next_tps": [round(avg + sg * k * a, 1) for k in tps[tp_hit:]],
                "events": ev, "plan": plan, "last_price": round(float(c[j]), 1),
            })
            break
        if pos > 1e-12:
            px = c[j]
            realized += sg * pos * (px - avg)
            fees += pos * px * fee
            ev.append({"date": D(j), "type": "exit", "kind": "time", "price": round(float(px), 1),
                       "pct": round(pos / qty * 100), "note": f"uscita a tempo ({p.max_hold} giorni)"})
            exit_reason = exit_reason or "time"
        notional = cost  # capitale effettivamente investito (somma pesi riempiti)
        pnl = realized - fees + funding
        trades.append({
            "signal_date": idx[i].date(), "exit_date": idx[j].date(), "side": side, "setup": setup[i],
            "days": j - i, "tranches": sum(filled), "avg_entry": round(avg, 1),
            "invested": round(notional, 3), "tp_hit": tp_hit, "exit": exit_reason,
            "pnl_pct_invested": pnl / notional * 100, "pnl_pct_capital": pnl * 100,
            "fees_pct": fees * 100, "funding_pct": funding * 100,
            "events": ev, "plan": plan,
        })
        i = j + p.cooldown
    return pd.DataFrame(trades)


def summary(t: pd.DataFrame, leverage: float = 1.0) -> dict:
    if not t.empty:
        t = t[t["exit"] != "open"]
    if t.empty:
        return {"trades": 0}
    pnl = t["pnl_pct_capital"] * leverage
    wins, losses = pnl[pnl > 0], pnl[pnl <= 0]
    eq = (1 + pnl / 100).cumprod()
    return {
        "trades": len(t),
        "win_rate": round(len(wins) / len(t) * 100, 1),
        "avg_win_%": round(float(wins.mean()), 2) if len(wins) else 0,
        "avg_loss_%": round(float(losses.mean()), 2) if len(losses) else 0,
        "profit_factor": round(float(wins.sum() / -losses.sum()), 2) if len(losses) and losses.sum() < 0 else float("inf"),
        "expectancy_%": round(float(pnl.mean()), 2),
        "total_return_%": round(float(eq.iloc[-1] - 1) * 100, 1),
        "max_dd_%": round(float(((eq / eq.cummax()) - 1).min()) * 100, 1),
        "avg_days": round(float(t["days"].mean()), 1),
        "worst_%": round(float(pnl.min()), 2),
        # win rate "pulito": solo trade chiusi da target, trailing o tempo in profitto (stop e pareggi non contano come vincite)
        "win_rate_clean": round(float(((t["exit"].isin(["tp", "trail", "time"])) & (pnl > 0)).mean() * 100), 1),
        "win_rate_1pct": round(float((t["pnl_pct_invested"] >= 1).mean() * 100), 1),
    }
