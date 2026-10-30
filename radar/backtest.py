"""Backtest giornaliero con DCA in entrata/uscita, commissioni e funding.

Convenzioni conservative con barre giornaliere:
- il segnale si calcola sulla chiusura di t, il primo ingresso è all'open di t+1
- nella stessa giornata i limit DCA si riempiono prima di controllare lo stop
- se nello stesso giorno si toccano stop e take profit si assume lo stop
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from .data import DATA_DIR
from .strategy import Params, compute_signals

FEES = {"spot": 0.001, "futures": 0.0005}  # per lato (taker)
_H1: dict | None = None


def hourly_bars() -> dict:
    """Candele orarie spot (data/spot_1h.csv, se presente) per giorno: servono solo a ordinare TP1 e stop a pareggio."""
    global _H1
    if _H1 is None:
        _H1 = {}
        path = DATA_DIR / "spot_1h.csv"
        if path.exists():
            h = pd.read_csv(path, index_col=0, parse_dates=True)
            for day, g in h.groupby(h.index.normalize()):
                _H1[day] = (g["high"].values, g["low"].values)
    return _H1


def run(f: pd.DataFrame, p: Params, market: str = "futures", start=None, end=None, signals: pd.DataFrame | None = None,
        intraday: dict | None = None) -> pd.DataFrame:
    s = compute_signals(f, p) if signals is None else signals
    h1 = hourly_bars() if intraday is None else intraday
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
        # percorso giornaliero mark-to-market (PnL in frazione del capitale a 1x, alla chiusura del giorno):
        # serve solo alla misura del drawdown reale, non cambia la logica del trade
        mtm: list = []
        # registro operativo del trade: segnale, piano, ogni ingresso e ogni uscita
        ev = [{"date": D(i), "type": "signal", "price": round(float(c[i]), 1),
               "note": f"segnale {setup[i]} alla chiusura"}]
        plan = {"entries": [round(float(lv), 1) for lv in levels], "weights": list(p.entry_weights),
                "stop": round(float(stop), 1), "atr": round(float(a), 1),
                "tp_atr": list(p.tp_atr), "tp_weights": list(p.tp_weights), "trail_atr": p.trail_atr}
        for j in range(i + 1, min(n, i + 1 + p.max_hold)):
            # 1) ingressi DCA
            # il target del giorno si calcola sul prezzo medio PRIMA dei limit riempiti oggi: dentro la giornata
            # il massimo può arrivare prima del calo che riempie la tranche (verificato su candele a 4 ore)
            q_prev, c_prev, filled_today = qty, cost, False
            for k, lv in enumerate(levels):
                if filled[k] or (k > 0 and j - (i + 1) >= p.entry_window) or tp_hit:
                    continue
                hit = (k == 0) or (sg == 1 and l[j] <= lv) or (sg == -1 and h[j] >= lv)
                if hit:
                    px = e0 if k == 0 else (min(lv, o[j]) if sg == 1 else max(lv, o[j]))
                    q = p.entry_weights[k] / px
                    filled[k] = True
                    if k == 0:  # il primo ingresso è all'apertura: precede tutto il resto della giornata
                        q_prev, c_prev = q_prev + q, c_prev + q * px
                    else:
                        filled_today = True
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
            avg_tp = (c_prev / q_prev) if (filled_today and q_prev > 0) else avg
            tp_before = tp_hit
            while tp_hit < len(tps):
                tp = avg_tp + sg * tps[tp_hit] * a
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
            # 3b) stop a pareggio messo oggi dal TP1: con le barre giornaliere si controllava solo da domani, e il trade
            # restava aperto 1-2 giorni in più (stesso PnL, ma bloccava i segnali successivi). Con le candele orarie
            # si verifica se dopo l'ora del TP1 il prezzo è tornato sullo stop nello stesso giorno.
            hl = h1.get(idx[j])
            if hl is not None and not (np.isclose(hl[0].max(), h[j], rtol=1e-6) and np.isclose(hl[1].min(), l[j], rtol=1e-6)):
                hl = None  # le candele orarie devono ricomporre la giornata (stessa fonte e stesso giorno)
            if tp_before == 0 and tp_hit == 1 and pos > 1e-12 and hl is not None:
                hh, ll = hl
                tp1 = avg_tp + sg * tps[0] * a
                k1 = int(np.argmax(hh >= tp1)) if sg == 1 else int(np.argmax(ll <= tp1))
                after = ll[k1 + 1:] <= stop if sg == 1 else hh[k1 + 1:] >= stop
                if after.any():
                    realized += sg * pos * (stop - avg)
                    fees += pos * stop * fee
                    exit_reason = "stop_be"
                    ev.append({"date": D(j), "type": "exit", "kind": exit_reason, "price": round(float(stop), 1),
                               "pct": round(pos / qty * 100), "note": "stop a pareggio (stesso giorno del TP1)"})
                    pos = 0
            # 4) trailing sul residuo dopo TP1
            best = max(best, c[j]) if sg == 1 else min(best, c[j])
            if tp_hit >= 1:
                trail = best - sg * p.trail_atr * a
                stop = max(stop, trail) if sg == 1 else min(stop, trail)
            if market == "futures":
                funding -= sg * pos * c[j] * fund[j]
            if qty > 0:
                mtm.append((D(j), float(realized - fees + funding + sg * pos * (c[j] - avg))))
            if pos <= 1e-12:
                exit_reason = exit_reason or "tp"
                break
        still_open = pos > 1e-12 and j == n - 1 and (j - i) < p.max_hold
        if still_open:
            pnl = realized - fees + funding + sg * pos * (c[j] - avg)
            if not mtm or mtm[-1][0] != D(j):
                mtm.append((D(j), float(pnl)))
            trades.append({
                "signal_date": idx[i].date(), "exit_date": None, "side": side, "setup": setup[i],
                "days": j - i, "tranches": sum(filled), "avg_entry": round(avg, 1),
                "invested": round(cost, 3), "tp_hit": tp_hit, "exit": "open",
                "pnl_pct_invested": pnl / cost * 100, "pnl_pct_capital": pnl * 100,
                "stop": round(stop, 1), "remaining": round(pos / qty, 3),
                "pending_entries": [round(lv, 1) for k, lv in enumerate(levels)
                                    if not filled[k] and not tp_hit and j - (i + 1) < p.entry_window],
                "next_tps": [round(avg + sg * k * a, 1) for k in tps[tp_hit:]],
                "events": ev, "plan": plan, "last_price": round(float(c[j]), 1), "mtm": mtm,
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
        if mtm and mtm[-1][0] == D(j):
            mtm[-1] = (D(j), float(pnl))  # il giorno di uscita vale il risultato finale
        else:
            mtm.append((D(j), float(pnl)))
        trades.append({
            "signal_date": idx[i].date(), "exit_date": idx[j].date(), "side": side, "setup": setup[i],
            "days": j - i, "tranches": sum(filled), "avg_entry": round(avg, 1),
            "invested": round(notional, 3), "tp_hit": tp_hit, "exit": exit_reason,
            "pnl_pct_invested": pnl / notional * 100, "pnl_pct_capital": pnl * 100,
            "fees_pct": fees * 100, "funding_pct": funding * 100,
            "events": ev, "plan": plan, "mtm": mtm,
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
