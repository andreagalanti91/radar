"""emergenti · motore della fase 2 (PREREG.md). Copia di radar.weekly.simulate (radar/weekly.py non si tocca) con:
- parametri esposti: stop_k, trail_k, span dell'EMA d'uscita (default 21 = W3.2), maschere d'ingresso per lato (domeniche);
- registrazione degli indici d'ingresso/uscita e dello stop di ogni giorno, per calcolare dopo l'esito con leva e liquidazione
  (outcome) e il portafoglio a budget (portfolio).
Con i parametri di default e la size di W3.2 deve riprodurre radar.weekly.simulate (controllo in check()).
Esito per 1 $ di margine con nozionale k $: valore = 1 + k·lato·(P/E − 1) − commissioni − funding; liquidazione (margine isolato)
quando il movimento avverso raggiunge 1/k − mantenimento, sui minimi/massimi giornalieri; alla liquidazione il margine è perso."""
from __future__ import annotations
import importlib.util, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402

def weekly_bars(f, exit_span=21):
    w = W.weekly_bars(f)
    w["ema_exit"] = w["ema21"] if exit_span == 21 else w["close"].ewm(span=exit_span, adjust=False).mean()
    return w

def _decide(wk, side, al, as_):
    if side:
        beyond = wk["close"] < wk["ema_exit"] if side > 0 else wk["close"] > wk["ema_exit"]
        if beyond: return ("exit", "ema")
        if wk["dist_long"] if side > 0 else wk["dist_short"]: return ("exit", "dist")
        return None
    if wk["long"] and al: return ("enter", 1)
    if wk["short"] and as_: return ("enter", -1)
    return None

def simulate(f, start, stop_k=W.STOP_K, trail_k=W.TRAIL_K, exit_span=21, allow_long=None, allow_short=None,
             fee_spot=W.FEE_SPOT, fee_perp=W.FEE_PERP, slip=W.SLIP, all_perp=False, capital=10000.0):
    """= radar.weekly.simulate (lev 1) + parametri. allow_long/allow_short: Serie booleane sulle domeniche (None = sempre)."""
    f = f[f["close"].notna()]
    w = weekly_bars(f, exit_span)
    idx = f.index
    O, H, L, C = (f[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, qty, cost, side, pend, tr = 1.0, 0.0, 0.0, 0, None, None
    frate, fperp = fee_perp, 1.0
    trades, eq = [], np.full(len(idx), np.nan)

    def close_all(px, i, reason):
        nonlocal cash, qty, cost, side, tr
        cash += qty * px - cost - abs(qty) * px * frate
        tr.update(exit=str(idx[i].date()), i_exit=i, exit_px=px, reason=reason, pnl=cash / tr["eq0"] - 1)
        trades.append(tr); tr, qty, cost, side = None, 0.0, 0.0, 0

    for i in range(t0, len(idx)):
        day = idx[i]
        if pend is not None:
            if pend[0] == "exit" and side:
                close_all(O[i] * (1 - slip * side), i, pend[1])
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = W.exposure(side, wk["close"], wk["atr"], 1.0) if stop_k == W.STOP_K else min(1.0, (W.R_LONG if side > 0 else W.R_SHORT) / (stop_k * wk["atr"] / wk["close"]))
                fs = 0.0 if all_perp else (min(lt, 1.0) / lt if side > 0 else 0.0)
                frate, fperp = fs * fee_spot + (1 - fs) * fee_perp, 1 - fs
                px = O[i] * (1 + slip * side)
                q = side * lt * cash / px
                qty, cost = q, q * px
                cash -= abs(q) * px * frate
                tr = dict(signal=str(pend[3].date()), entry=str(day.date()), i_entry=i, side="long" if side > 0 else "short",
                          entry_px=px, atr=float(wk["atr"]), expo=lt, flow=float(wk["flow"]), eq0=cash + abs(q) * px * frate,
                          stop0=float(wk["close"] - side * stop_k * wk["atr"]), best=O[i], curatr=float(wk["atr"]), stops=[])
                tr["stop"] = tr["stop0"]
            pend = None
        if side:
            tl = tr["best"] - side * trail_k * tr["curatr"]
            stop = max(tr["stop"], tl) if side > 0 else min(tr["stop"], tl)
            tr["stop"] = stop; tr["stops"].append(stop)
            if (side > 0 and L[i] <= stop) or (side < 0 and H[i] >= stop):
                px = (min(O[i], stop) if side > 0 else max(O[i], stop)) * (1 - slip * side)
                close_all(px, i, "stop" if stop == tr["stop0"] else "trail")
            else:
                cash -= fperp * qty * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
        eq[i] = cash + (qty * C[i] - cost if side else 0.0)
        if day.dayofweek == 6 and day in w.index:
            wk = w.loc[day]
            if side: tr["curatr"] = float(wk["atr"])
            al = True if allow_long is None else bool(allow_long.get(day, False))
            as_ = True if allow_short is None else bool(allow_short.get(day, False))
            d = _decide(wk, side, al, as_)
            pend = d + (wk, day) if d else None
    out = {"trades": trades, "equity": pd.Series(eq[t0:], idx[t0:]) * capital, "open": None, "index": idx}
    if side:
        i = len(idx) - 1
        tr.update(exit=None, i_exit=i, exit_px=C[i], reason="open", pnl=(eq[i] - abs(qty) * C[i] * frate) / tr["eq0"] - 1)
        out["open"] = tr
    return out

def all_trades(o):
    return o["trades"] + ([o["open"]] if o["open"] else [])

def outcome(tr, A, k, fee=0.002, mmr=0.01, max_days=None):
    """Esito di un trade per 1 $ di margine con nozionale k. A: dict di array (O,H,L,C,FU) sulla stessa base d'indice di tr.
    fee = costo per lato (commissione + slittamento) oltre allo slittamento già nel prezzo d'ingresso/uscita del motore
    (il motore usa slittamento 0,1%; qui si aggiunge la commissione: fee totale 0,2% = 0,1% + 0,1%).
    Restituisce (i0, i1, v): v[j] = valore del margine alla chiusura del giorno i0+j; l'ultimo valore è al netto dell'uscita.
    max_days: uscita forzata all'apertura dopo max_days giorni (descrittivo)."""
    sd = 1 if tr["side"] == "long" else -1; i0, i1 = tr["i_entry"], tr["i_exit"]; E = tr["entry_px"]
    reason, X = tr["reason"], tr["exit_px"]; stops = tr.get("stops") or []
    O, H, L, C, FU = (A[c] for c in ("O", "H", "L", "C", "FU"))
    if max_days is not None and i1 - i0 > max_days:
        i1 = i0 + max_days; reason = "tempo"; X = O[i1] * (1 - 0.001 * sd)
    comm = fee - 0.001
    n = i1 - i0 + 1
    c = C[i0:i1 + 1].copy(); c = pd.Series(c).ffill().to_numpy()
    fu = np.nan_to_num(FU[i0:i1 + 1]) * sd * k * c / E
    cumf = np.cumsum(fu)
    v = 1 + k * sd * (c / E - 1) - k * comm - cumf
    q = 1.0 / k - mmr
    liq = E * (1 - q) if sd > 0 else E * (1 + q)
    for j in range(n):
        i = i0 + j; o, h, l = O[i], H[i], L[i]
        if not np.isfinite(o): continue
        intraday_exit = (j == n - 1) and reason in ("stop", "trail")
        at_open_exit = (j == n - 1) and reason in ("ema", "dist", "tempo")
        if (sd > 0 and o <= liq) or (sd < 0 and o >= liq):
            return i0, i0 + j, np.r_[v[:j], 0.0], True
        if at_open_exit: break
        hit = (l <= liq) if sd > 0 else (h >= liq)
        if hit and np.isfinite(l):
            st = stops[j] if j < len(stops) else None
            if intraday_exit and st is not None and ((sd > 0 and st > liq) or (sd < 0 and st < liq)): break
            return i0, i0 + j, np.r_[v[:j], 0.0], True
    # uscita: prezzo del motore, commissione d'uscita; funding fino al giorno prima
    fin = 1 + k * sd * (X / E - 1) - k * comm - k * comm * X / E - (cumf[-2] if n > 1 else 0.0)
    if reason == "open": fin = 1 + k * sd * (c[-1] / E - 1) - k * comm - k * comm * c[-1] / E - cumf[-1]
    v[-1] = fin
    return i0, i1, v, False

def portfolio(cands, ndays, slots=5, budget=10000.0, start_i=0):
    """cands: lista di dict con i0, i1, v (array), pri (priorità). Margine = min(equity/slots, cassa) all'ingresso;
    massimo `slots` posizioni; esclusi i segnali in eccesso. Restituisce (equity giornaliera da start_i, lista dei presi)."""
    cands = sorted(cands, key=lambda c: (c["i0"], -c["pri"]))
    cash, opn, taken = budget, [], []
    delta = np.zeros(ndays + 1); contrib = np.zeros(ndays + 1)
    for c in cands:
        t = c["i0"]
        still = []
        for p in opn:
            if p["i1"] <= t and not (p["i1"] == t and p["liq_or_intraday"]):
                cash += p["m"] * p["v"][-1]
            else: still.append(p)
        opn = still
        if len(opn) >= slots: continue
        eqb = cash + sum(p["m"] * (p["v"][t - 1 - p["i0"]] if t - 1 >= p["i0"] else 1.0) for p in opn)
        m = min(eqb / slots, cash)
        if m <= 0: continue
        cash -= m
        p = dict(c, m=m, liq_or_intraday=c.get("intra", False)); opn.append(p); taken.append(p)
    for p in taken:
        a, b, v, m = p["i0"], p["i1"], p["v"], p["m"]
        delta[a] -= m; delta[b] += m * v[-1]
        if b > a: contrib[a:b] += m * v[:-1]
    eq = budget + np.cumsum(delta) + contrib
    return eq[start_i:ndays], taken

def check():
    """Controllo del motore: con i parametri di default = radar.weekly.simulate su BTC ed ETH (dati di data/coins)."""
    spec = importlib.util.spec_from_file_location("w32c", HERE.parent / "w32_asset2" / "crypto" / "counts.py")
    C = importlib.util.module_from_spec(spec); spec.loader.exec_module(C); C.D = HERE / "data" / "coins"
    out = {}
    for t in ("BTC", "ETH"):
        f = C.feats(t); a = W.simulate(f, start="2021-01-01"); b = simulate(f, start="2021-01-01")
        same = len(a["trades"]) == len(b["trades"]) and all(x["entry"] == y["entry"] and x["exit"] == y["exit"] for x, y in zip(a["trades"], b["trades"]))
        out[t] = (round(float(a["equity"].iloc[-1])), round(float(b["equity"].iloc[-1])), same)
    return out

if __name__ == "__main__":
    print(check())
