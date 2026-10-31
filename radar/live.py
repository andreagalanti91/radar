"""Valutazione dei segnali reali con la strategia v2 (promossa il 31/10/2026, approvata dall'utente).

v2 (ricerca "Notte · ora 01:47", motore in radar/paper.py):
- trigger = setup giornalieri (compute_signals) alla chiusura UTC
- conferma: prima chiusura 4h oltre il massimo (short: sotto il minimo) delle 2 candele 4h precedenti, entro 72h;
  ingresso a mercato all'apertura della barra 4h successiva
- 2 livelli: 40% al prezzo di conferma, 60% limit a −0,5 ATR (valido 7 giorni); stop 1 ATR dall'ingresso;
  TP unico a +1R dal prezzo medio; tenuta massima 14 giorni
- rischio = base × (0,5 + 1,5·clip(segno·DT_mix, 0, 0,15)/0,15) × (0,6 se long sotto la SMA 40 settimane);
  leva = min(5, rischio / distanza dello stop)
Rischio base dal vivo RADAR_RISK (predefinito 4,67%, valore validato con slippage 0,2%; ricerca 5,24%).
Il rischio di ogni trade reale si congela alla conferma (data/state.json, v2_risk_frozen).
La vecchia strategia giornaliera resta in radar/backtest.py per la ricerca.
"""
from __future__ import annotations

import json
import math
import os

import numpy as np
import pandas as pd

from . import paper
from .data import DATA_DIR
from .zones import latest_zone
from .strategy import SETUPS, Params, compute_signals, conditions, explain

STATE_FILE = DATA_DIR / "state.json"
BACKTEST_START = "2022-03-01"   # le metrics (long/short ratio) partono da dic 2021 + warm-up
TEST_START = "2024-01-01"       # walk-forward: 2024–25 e 2026 fuori dalla scelta dei parametri
LIVE_START = "2026-10-31"       # da qui i segnali reali sono quelli di v2
RISK = float(os.environ.get("RADAR_RISK", "0.043"))
CAPITAL = float(os.environ.get("RADAR_CAPITAL", "50000"))
PERIODS = [("2022–23", "2022-03-01", "2023-12-31"), ("2024–25", "2024-01-01", "2025-12-31"),
           ("2026", "2026-01-01", "2026-12-31"), ("Totale", "2022-03-01", "2099-12-31")]
MULTS = (1, 2, 5)               # size moltiplicata rispetto al piano v2 (1x = piano)


def _clean(x):
    if isinstance(x, float) and (math.isnan(x) or math.isinf(x)):
        return None
    if hasattr(x, "item"):
        return _clean(x.item())
    if isinstance(x, dict):
        return {k: _clean(v) for k, v in x.items()}
    if isinstance(x, (list, tuple)):
        return [_clean(v) for v in x]
    if hasattr(x, "isoformat"):
        return x.isoformat()
    return x


def _state() -> dict:
    try:
        return json.loads(STATE_FILE.read_text())
    except (OSError, ValueError):
        return {}


def plan(o: dict, risk_range=None, capital: float = CAPITAL) -> dict:
    """Piano v2 in prezzi e dollari. `o` = stato di paper.simulate (conferma / ingresso / aperto).
    In conferma l'ingresso è stimato alla soglia; il rischio è un intervallo finché non si conosce il delta taker."""
    sg, a = (1 if o["side"] == "long" else -1), float(o["atr"])
    e = float(o["entry"]) if o["status"] == "aperto" else float(o["entry_est"])
    lv = [e, e - sg * paper.STEP * a]
    stop = lv[1] - sg * paper.STOP * a
    pavg = 1.0 / (paper.W[0] / lv[0] + paper.W[1] / lv[1])
    rd = abs(pavg - stop)
    stop_pct = rd / pavg + 2 * paper.FEE + paper.SLIP
    out = dict(entry=round(e, 2), limit=round(lv[1], 2), stop=round(stop, 2), avg_full=round(pavg, 2),
               tp_full=round(pavg + sg * paper.TP_R * rd, 2), tp_first=round(e + sg * paper.TP_R * rd, 2),
               stop_pct=round(stop_pct * 100, 2), weights=list(paper.W), capital=capital)
    if o["status"] == "aperto":
        out["tp"] = float(o["tp"])   # TP attuale sul medio effettivo
    rk = o.get("risk")
    if rk is None and risk_range:
        lo, hi = risk_range
        out.update(risk_lo=round(lo * 100, 2), risk_hi=round(hi * 100, 2),
                   lev_lo=round(min(paper.CAP, lo / stop_pct), 2), lev_hi=round(min(paper.CAP, hi / stop_pct), 2))
    if rk is not None:
        N = min(paper.CAP, rk / stop_pct)
        nz = capital * N
        out.update(risk=round(rk * 100, 2), lev=round(N, 2), notional=round(nz, 0),
                   t1_usd=round(nz * paper.W[0], 0), t2_usd=round(nz * paper.W[1], 0),
                   t1_btc=round(nz * paper.W[0] / lv[0], 4), t2_btc=round(nz * paper.W[1] / lv[1], 4),
                   loss_usd=round(nz * stop_pct, 0), gain_usd=round(nz * (rd / pavg - 2 * paper.FEE), 0))
    return out


def _period(trades: list, eq: pd.Series, a: str, b: str) -> dict:
    """Statistiche di un periodo: trade per data del segnale, rendimento e DD sull'equity giornaliera."""
    t = [x for x in trades if a <= x["date"] <= b]
    pn = np.array([x["pnl_pct"] for x in t]) if t else np.zeros(0)
    e = eq[(eq.index >= pd.Timestamp(a)) & (eq.index <= pd.Timestamp(b))]
    before = eq[eq.index < pd.Timestamp(a)]
    e0 = float(before.iloc[-1]) if len(before) else (float(e.iloc[0]) if len(e) else 1.0)
    ee = pd.concat([pd.Series([e0]), e.reset_index(drop=True)])
    win, loss = pn[pn > 0], pn[pn <= 0]
    return {
        "trades": len(t),
        "win_rate": round(float((pn > 0).mean() * 100), 1) if len(pn) else None,
        "win_rate_1pct": round(float((pn > 1).mean() * 100), 1) if len(pn) else None,
        "profit_factor": round(float(win.sum() / -loss.sum()), 2) if len(loss) and loss.sum() < 0 else None,
        "avg_win_%": round(float(win.mean()), 2) if len(win) else 0.0,
        "avg_loss_%": round(float(loss.mean()), 2) if len(loss) else 0.0,
        "expectancy_%": round(float(pn.mean()), 2) if len(pn) else 0.0,
        "total_return_%": round(float(ee.iloc[-1] / e0 - 1) * 100, 1) if len(e) else 0.0,
        "max_dd_%": round(float((ee / ee.cummax() - 1).min()) * 100, 1) if len(e) else 0.0,
        "avg_days": round(float(np.mean([x["days"] for x in t])), 1) if t else 0.0,
        "avg_lev": round(float(np.mean([x["N"] for x in t])), 2) if t else 0.0,
    }


def _mult(trades: list, m: float, cap: float = 10000.0) -> dict:
    """Size moltiplicata per `m` trade per trade, con il tetto di esposizione a 5x del conto (come dal vivo):
    rendimento, DD per trade, peggior trade."""
    e, peak, dd, curve = 1.0, 1.0, 0.0, []
    mm = [min(m, 5.0 / t["N"]) if t.get("N") else m for t in trades]
    for t, k in zip(trades, mm):
        e *= 1 + k * t["pnl_pct"] / 100
        peak, dd = max(peak, e), min(dd, e / max(peak, e) - 1)
        curve.append({"date": t["exit_date"], "eq": round(e, 4)})
    pn = [k * t["pnl_pct"] for t, k in zip(trades, mm)]
    return {"total_return_%": round((e - 1) * 100, 1), "max_dd_%": round(dd * 100, 1),
            "worst_%": round(min(pn), 2) if pn else 0.0, "expectancy_%": round(float(np.mean(pn)), 2) if pn else 0.0,
            "final_10k": round(cap * e, 0), "curve": curve}


def _dash_trade(t: dict, s: pd.DataFrame, p: Params) -> dict:
    """Trade v2 nel formato della dashboard (timeline con segnale, ingresso, limit, uscita)."""
    d = pd.Timestamp(t["date"])
    sd = t["date"]
    ev = [{"type": "signal", "date": sd, "price": float(s.at[d, "close"]) if d in s.index else t["entry"],
           "note": f"setup {t['setup']} alla chiusura giornaliera"},
          {"type": "entry", "date": t["entry_time"][:10], "price": t["entry"], "pct": 40,
           "note": f"conferma 4h · ingresso alle {t['entry_time'][11:16]} UTC"}]
    if t.get("fill_time"):
        ev.append({"type": "entry", "date": t["fill_time"][:10], "price": t["levels"][1], "pct": 60,
                   "note": "limit a −0,5 ATR eseguito"})
    if t["exit"] != "open":
        ev.append({"type": "exit", "kind": t["exit"], "date": t["exit_date"], "price": t["exit_px"], "pct": 100,
                   "note": {"tp": "take profit +1R dal medio", "stop": "stop 1 ATR dall'ingresso",
                            "time": "uscita dopo 14 giorni"}.get(t["exit"], "")})
    days = (pd.Timestamp(t["exit_date"]) - d).days
    return dict(t, signal_date=sd, days=days, tranches=t["fills"], pnl_pct_capital=t["pnl_pct"],
                pnl_pct_invested=round(t["pnl_unit"] * 100, 2), avg_entry=t["avg"], invested=t["N"], events=ev,
                why=explain(s.loc[d], t["setup"], p) if d in s.index else "", plan={"stop": t["stop"], "atr": t["atr"]})


def _now(o: dict | None, h4: pd.DataFrame, fn) -> dict:
    """Stato attuale di v2: nessuno / conferma / ingresso / aperto, con il piano completo."""
    if not o:
        return {"status": "nessuno"}
    o = dict(o)
    o.setdefault("signal_date", o.get("date"))
    sg = 1 if o["side"] == "long" else -1
    nxt = h4.index[-1] + pd.Timedelta(hours=4)
    rr = None
    if o["status"] == "conferma":
        o["entry_est"] = o["trigger"]
        r0, info = fn(sg, pd.Timestamp(o["signal_date"]), pd.Timestamp("1900-01-01"))   # DT = 0: rischio minimo
        rr = (r0, r0 * (0.5 + paper.V2_K) / 0.5)
        o["below_sma40w"] = info["below_sma40w"]
    elif o["status"] == "ingresso":
        o["entry_est"] = float(h4["close"].iloc[-1])   # ingresso a mercato all'apertura della barra in corso
        o["entry_time"] = str(nxt)
        o["limit_expiry"] = str(nxt + pd.Timedelta(days=paper.LIM_DAYS))
        o["time_exit"] = str(nxt + pd.Timedelta(days=paper.HOLD))
    if o["status"] == "aperto":
        o["fills"] = int(sum(o["filled"]))
        o["pnl_pct_invested"] = round(o.get("pnl_unit", 0.0) * 100, 2)
    o["plan"] = plan(o, rr)
    o["last_4h"] = str(h4.index[-1])
    return {k: v for k, v in o.items() if k not in ("pnl_unit", "path")}


def evaluate(f: pd.DataFrame, p: Params | None = None, h4: pd.DataFrame | None = None,
             frozen: dict | None = None) -> dict:
    """Report giornaliero/orario: mercato, setup, stato di v2 e storico v2 dal 2022-03.
    `h4` = candele 4h (predefinito: dal vivo con le ore chiuse di oggi); `frozen` = rischi congelati dei trade reali."""
    p = p or Params()
    s = compute_signals(f, p)
    s = s.loc[: s["score"].last_valid_index()]  # ultimo giorno con dati derivati completi
    f = f.loc[: s.index[-1]]
    last = s.iloc[-1]
    downtrend = bool((last["close"] < last["sma200"]) and (last["sma50"] < last["sma200"]))
    regime = "rialzista" if bool(last["up"]) else "ribassista" if downtrend else "neutrale"

    # ---- motore v2: storico ricalcolato, rischio dei trade reali congelato alla conferma
    h4 = paper.candles_4h(live=True) if h4 is None else h4
    frozen = _state().get("v2_risk_frozen", {}) if frozen is None else frozen
    fn = paper.v2_risk(f, h4, RISK)
    live_fn = paper.frozen_risk(fn, frozen)
    risk_fn = lambda sg, d, tc: live_fn(sg, d, tc) if d >= pd.Timestamp(LIVE_START) else fn(sg, d, tc)  # noqa: E731
    r = paper.simulate(f, h4, BACKTEST_START, capital=10000.0, risk_fn=risk_fn)
    eq = r["equity"] / 10000.0
    now = _now(r["open"], h4, fn)
    if now["status"] != "nessuno" and now["signal_date"] in s.index.strftime("%Y-%m-%d"):
        d = pd.Timestamp(now["signal_date"])
        now.update(setup_label=SETUPS.get(now["setup"], ("", ""))[1], why=explain(s.loc[d], now["setup"], p),
                   signal_close=float(s.at[d, "close"]))
    trades = [_dash_trade(t, s, p) for t in r["trades"]]
    if r["open"] and r["open"]["status"] == "aperto":
        ot = dict(r["open"], exit="open", exit_date=str(h4.index[-1].date()), exit_px=None)
        trades.append(_dash_trade(ot, s, p))
    closed = [t for t in trades if t["exit"] != "open"]

    stats = {"periods": {k: _period(closed, eq, a, b) for k, a, b in PERIODS}}
    stats["years"] = {str(y): _period(closed, eq, f"{y}-01-01", f"{y}-12-31") for y in range(2022, s.index[-1].year + 1)}
    stats["leverage"] = {str(m): _mult(closed, m) for m in MULTS}
    stats["by_setup"] = {
        k: {"trades": len(g), "win_rate": round(float(np.mean([x["pnl_pct"] > 0 for x in g]) * 100), 1),
            "expectancy_%": round(float(np.mean([x["pnl_pct"] for x in g])), 2), "label": SETUPS[k][1], "side": SETUPS[k][0]}
        for k in SETUPS if (g := [x for x in closed if x["setup"] == k])
    }
    stats["by_exit"] = {k: {"n": len(g), "avg": round(float(np.mean([x["pnl_pct"] for x in g])), 2)}
                        for k in ("tp", "stop", "time") if (g := [x for x in closed if x["exit"] == k])}
    years = (s.index[-1] - pd.Timestamp(BACKTEST_START)).days / 365.25
    stats["trades_per_year"] = round(len(closed) / years, 1)
    stats["risk"] = {"base": RISK, "k": paper.V2_K, "clip": paper.V2_CLIP, "m_long_sotto_sma40w": paper.V2_M, "cap": paper.CAP,
                     "min_%": round(RISK * 0.5 * paper.V2_M * 100, 2), "max_%": round(RISK * (0.5 + paper.V2_K) * 100, 2),
                     "avg_%": round(float(np.mean([x["risk"] for x in closed])) * 100, 2) if closed else None}

    # stato attuale di ciascun setup (per la checklist)
    cond = conditions(f.loc[: s.index[-1]], p)
    detail = {
        "flow": f"score {last['score']:+.2f} (soglia +{p.flow_threshold})",
        "capit": f"drawdown 30g {last['dd30']*100:.1f}% (≤ {p.capit_dd*100:.0f}%) · OI 7g {last['oi_chg7']*100:+.1f}% (≤ {p.capit_oi*100:.0f}%)",
        "fundneg": f"funding 7g {last['funding7']*100:+.4f}% per giorno (< 0)",
        "brk": f"distanza dal max 20g {last['brk20']*100:+.1f}% · CVD perp {last['pf14z']:+.2f}σ (> +{p.brk_flow}) · trend {'ok' if last['up'] else 'no'}",
        "sflow": f"score {last['score']:+.2f} (soglia −{p.flow_threshold}) · regime {'ribassista' if last['down'] else 'non ribassista'}",
        "sfund": f"funding z {last['funding_z']:+.2f} (soglia +{p.sfund_z}) · regime {'ribassista' if last['down'] else 'non ribassista'}",
    }
    checklist = [{"setup": k, "side": side, "label": label, "active": bool(cond[k].iloc[-1]), "detail": detail[k]}
                 for k, (side, label) in SETUPS.items()]

    hist = s[s.index >= pd.Timestamp(BACKTEST_START)]
    equity = {"1x": [{"date": str(d.date()), "eq": round(float(v), 4)} for d, v in eq.items()],
              **{f"{m}x": stats["leverage"][str(m)].pop("curve") for m in MULTS if m != 1},
              "btc": [{"date": str(d.date()), "eq": round(float(v / hist["close"].iloc[0]), 4)} for d, v in hist["close"].items()]}
    stats["leverage"]["1"].pop("curve")
    stats["leverage"]["1"]["max_dd_daily_%"] = stats["periods"]["Totale"]["max_dd_%"]
    return _clean({
        "date": str(last.name.date()),
        "price": float(last["close"]),
        "score": float(last["score"]),
        "threshold": p.flow_threshold,
        "regime": regime,
        "components": {
            "perp_flow_z": float(last["pf14z"]),
            "retail_ls_z": float(last["ls_z"]),
            "perp_flow14": float(last["perp_flow14"]),
            "spot_flow14": float(last["spot_flow14"]),
            "global_ls": float(last["global_ls"]),
            "funding7_annual_pct": float(last["funding7"] * 365 * 100),
            "oi_chg7_pct": float(last["oi_chg7"] * 100),
            "basis_pct": float(last["basis"] * 100),
            "fng": float(last["fng"]),
            "atr": float(last["atr"]),
            "atr_pct": float(last["atr_pct"] * 100),
            "sma200": float(last["sma200"]),
        },
        "v2": now,
        "risk_frozen": frozen,
        "zone": latest_zone(f),
        "checklist": checklist,
        "equity": equity,
        "stats": stats,
        "params": {"weights": list(paper.W), "step_atr": paper.STEP, "stop_atr": paper.STEP + paper.STOP, "tp_r": paper.TP_R,
                   "hold_days": paper.HOLD, "limit_days": paper.LIM_DAYS, "window_h": 4 * paper.WIN, "cap": paper.CAP,
                   "risk": RISK, "capital": CAPITAL},
        "trades": {"futures": trades, "live": [t for t in trades if t["signal_date"] >= LIVE_START]},
        "live_start": LIVE_START,
        "updated_4h": str(h4.index[-1] + pd.Timedelta(hours=4)),
        "series": {
            "date": [str(d.date()) for d in hist.index],
            "open": hist["open"].round(1).tolist(), "high": hist["high"].round(1).tolist(),
            "low": hist["low"].round(1).tolist(), "close": hist["close"].round(1).tolist(),
            "score": hist["score"].round(3).tolist(),
            "sma200": hist["sma200"].round(1).tolist(),
        },
    })


def _closed_for(report: dict, sd: str) -> dict | None:
    return next((t for t in report["trades"]["futures"] if t["signal_date"] == sd and t["exit"] != "open"), None)


def diff_events(report: dict, prev: dict | None = None) -> list[dict]:
    """Eventi nuovi rispetto allo stato salvato: segnale giornaliero, ingresso confermato, limit eseguito,
    uscita (TP, stop, tempo) e segnale scaduto senza conferma."""
    prev = _state() if prev is None else prev
    old, cur = prev.get("v2") or {"status": "nessuno"}, report["v2"]
    events = []
    osd, csd = old.get("signal_date"), cur.get("signal_date")
    if cur["status"] != "nessuno" and csd != prev.get("last_signal_date") and csd != osd:
        events.append({"type": "signal", "v2": cur})
    if cur["status"] in ("ingresso", "aperto") and not (osd == csd and old["status"] in ("ingresso", "aperto")):
        events.append({"type": "entry", "v2": cur})
    if cur["status"] == "aperto" and osd == csd and (cur.get("fills") or 1) > (old.get("fills") or 1):
        events.append({"type": "dca_fill", "v2": cur})
    if old["status"] != "nessuno" and (csd != osd or cur["status"] == "nessuno"):
        t = _closed_for(report, osd)
        if t:
            if old["status"] == "conferma":   # ingresso e uscita tra due controlli
                events.append({"type": "entry", "v2": dict(t, status="aperto", signal_date=osd)})
            events.append({"type": t["exit"], "trade": t})
        elif old["status"] == "conferma":
            events.append({"type": "expired", "v2": old})
    return events


def save_state(report: dict) -> None:
    prev = _state()
    cur = report["v2"]
    state = dict(prev, date=report["date"],
                 last_signal_date=cur.get("signal_date") or prev.get("last_signal_date"),
                 v2={k: cur.get(k) for k in ("status", "signal_date", "side", "fills", "trigger", "deadline", "setup")},
                 v2_risk_frozen=report.get("risk_frozen", {}))
    state.pop("open", None)   # stato della vecchia strategia giornaliera
    STATE_FILE.write_text(json.dumps(_clean(state), indent=2, default=str))
