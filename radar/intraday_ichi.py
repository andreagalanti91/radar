"""Intraday · Ichimoku 4h su crypto (su carta, alert Telegram, esecuzione manuale).

Regola ICHI_tk della ricerca intraday (/tmp/radar-work/intra, lib.py + eng.py; selezionata in campione 2021-23, giudicata fuori
campione 2024-26: +0,14R medio, PF 1,23, WR 37%, 86% degli asset positivi):
- candele 4h UTC; Tenkan 9 = (max+min)/2 su 9 barre, Kijun 26 = idem su 26, Senkou A = (Tenkan+Kijun)/2 spostata avanti di 26,
  Senkou B = (max+min)/2 su 52 spostata avanti di 26 (la nube "sotto" la barra t è calcolata con i dati fino a t-26);
- LONG: alla chiusura della barra t la Tenkan incrocia sopra la Kijun (ten>kij e alla barra prima ten<=kij) e la chiusura è
  sopra la nube (sopra max(Senkou A, Senkou B)); SHORT speculare (incrocio sotto, chiusura sotto min(A, B));
- ingresso all'apertura della barra t+1; stop 2 ATR14 (Wilder, della barra del segnale) dal prezzo d'ingresso; target 3R;
  uscita a tempo alla chiusura della 48a barra; stop e target nella stessa barra -> conta lo stop; gap oltre lo stop -> esce
  all'apertura; una posizione per asset alla volta (i segnali durante una posizione si ignorano: il nuovo ingresso deve cadere
  dopo la barra d'uscita);
- costi: 0,05% commissione + 0,03% slippage per lato (0,05% di slippage sulle uscite a stop) = 0,08% per lato, 0,10% sullo stop.
  Funding IGNORATO (la ricerca lo sommava sui perp: in media pesa pochi centesimi di R; qui i dati sono spot);
- 10x su tutto il capitale: rendimento del conto = 10 x rendimento del trade; liquidazione (-100%) se l'escursione avversa arriva
  al 9,5% prima dello stop (margine di mantenimento ~0,5%).

Dati: klines SPOT 4h da data-api.binance.vision (i runner GitHub sono negli USA, fapi può rispondere 451), cache incrementale in
data/intra/<SYM>_4h.csv con le sole barre chiuse. I perp seguono lo stesso prezzo entro pochi decimi di %.
La barra in corso (scaricata a ogni giro, non salvata) serve solo a: prezzo d'ingresso reale (apertura dopo il segnale) e
tocchi di stop/target già avvenuti; segnali e uscite a tempo usano solo barre chiuse.
"""
from __future__ import annotations

import os
import time
from pathlib import Path

import numpy as np
import pandas as pd
import requests

ROOT = Path(__file__).resolve().parent.parent
DIR = ROOT / "data" / "intra"
KLINES = "https://data-api.binance.vision/api/v3/klines"
ASSETS = ["BTC", "ETH", "SOL", "BNB", "XRP", "DOGE", "LINK", "ADA", "AVAX", "LTC"]
START = "2021-01-01"
BAR = pd.Timedelta(hours=4)
K_STOP, TGT_R, HOLD = 2.0, 3.0, 48
FEE_IN, FEE_OUT, FEE_STOP = 0.0008, 0.0008, 0.0010     # commissione + slippage per lato
LIQ, MAX_LEV = 0.095, 10.0
CHART_BARS = 540                                        # ~90 giorni di candele 4h in dashboard
REASON = {"tgt": "Target 3R", "stop": "Stop", "time": "Uscita a tempo", "open": "Aperto"}


# ----------------------------------------------------------------------------------------------------------------- dati
def _get(sym: str, start_ms: int) -> list:
    for k in range(3):
        try:
            r = requests.get(KLINES, params={"symbol": sym, "interval": "4h", "startTime": start_ms, "limit": 1000}, timeout=20)
            r.raise_for_status()
            return r.json()
        except Exception as e:  # noqa: BLE001
            if k == 2:
                raise
            print(f"[intra] {sym} {type(e).__name__}, riprovo")
            time.sleep(2)
    return []


def _frame(rows: list) -> pd.DataFrame:
    d = pd.DataFrame([r[:5] for r in rows], columns=["t", "open", "high", "low", "close"])
    d["t"] = pd.to_datetime(d["t"], unit="ms")
    return d.set_index("t").astype(float)


def update(asset: str, now: pd.Timestamp | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Aggiorna la cache delle barre 4h chiuse (scarica solo le nuove). Ritorna (barre chiuse, barra in corso o vuoto)."""
    DIR.mkdir(parents=True, exist_ok=True)
    f, sym = DIR / f"{asset}_4h.csv", asset + "USDT"
    now = now or pd.Timestamp.utcnow().tz_localize(None)
    d = pd.read_csv(f, index_col="t", parse_dates=["t"]) if f.exists() else pd.DataFrame()
    start = (d.index[-1] + BAR) if len(d) else pd.Timestamp(START)
    new = []
    while True:
        rows = _get(sym, int(start.timestamp() * 1000))
        if not rows:
            break
        new += rows
        if len(rows) < 1000:
            break
        start = pd.Timestamp(rows[-1][0], unit="ms") + BAR
    live = pd.DataFrame()
    if new:
        n = _frame(new)
        live = n[n.index + BAR > now]
        n = n[n.index + BAR <= now]
        if len(n):
            d = pd.concat([d, n]) if len(d) else n
            d = d[~d.index.duplicated(keep="last")].sort_index()
            d.to_csv(f, index_label="t", float_format="%.10g")
    return d, live


def load(asset: str) -> pd.DataFrame:
    f = DIR / f"{asset}_4h.csv"
    return pd.read_csv(f, index_col="t", parse_dates=["t"]) if f.exists() else pd.DataFrame()


# ----------------------------------------------------------------------------------------------------------- indicatori
def indicators(d: pd.DataFrame) -> pd.DataFrame:
    """Tenkan, Kijun, Senkou A/B (già spostate di 26: valore della nube sotto la barra), ATR14 Wilder. Come lib.py."""
    h, l, c = d["high"], d["low"], d["close"]
    out = pd.DataFrame(index=d.index)
    out["ten"] = (h.rolling(9).max() + l.rolling(9).min()) / 2
    out["kij"] = (h.rolling(26).max() + l.rolling(26).min()) / 2
    out["sa_raw"] = (out["ten"] + out["kij"]) / 2                      # valori da proiettare 26 barre avanti
    out["sb_raw"] = (h.rolling(52).max() + l.rolling(52).min()) / 2
    out["sa"], out["sb"] = out["sa_raw"].shift(26), out["sb_raw"].shift(26)
    tr = pd.concat([h - l, (h - c.shift()).abs(), (l - c.shift()).abs()], axis=1).max(axis=1)
    out["atr"] = tr.ewm(alpha=1 / 14, adjust=False, min_periods=14).mean()
    return out


def signals(d: pd.DataFrame, ind: pd.DataFrame | None = None) -> np.ndarray:
    """+1 long, -1 short, 0 nulla alla chiusura di ogni barra (solo dati fino a quella barra)."""
    ind = indicators(d) if ind is None else ind
    c, ten, kij = d["close"], ind["ten"], ind["kij"]
    ctop, cbot = np.maximum(ind["sa"], ind["sb"]), np.minimum(ind["sa"], ind["sb"])
    up = (ten > kij) & (ten.shift() <= kij.shift()) & (c > ctop)
    dn = (ten < kij) & (ten.shift() >= kij.shift()) & (c < cbot)
    return up.fillna(False).astype(np.int8).values - dn.fillna(False).astype(np.int8).values


# ------------------------------------------------------------------------------------------------------------- backtest
def backtest(d: pd.DataFrame, live: pd.DataFrame | None = None, start: str = START) -> list[dict]:
    """Trade della regola su barre chiuse `d` (+ barra in corso `live` solo per ingresso e tocchi stop/target).
    L'ultimo elemento può essere un trade 'open' (in corso) o 'pending' (segnale sull'ultima barra chiusa, ingresso alla
    prossima apertura non ancora nota)."""
    if len(d) < 80:
        return []
    ind = indicators(d)
    sig = signals(d, ind)
    nc = len(d)
    full = pd.concat([d, live]) if live is not None and len(live) else d
    o, h, l, c = (full[k].values for k in ("open", "high", "low", "close"))
    ts, atr, n = full.index, ind["atr"].values, len(full)
    t0 = pd.Timestamp(start)
    out, nxt = [], 0
    for t in np.flatnonzero(sig):
        e = t + 1
        if e < nxt or ts[min(e, n - 1)] < t0 and e < n or np.isnan(atr[t]):
            continue
        dr = int(sig[t])
        if e >= n:      # segnale sull'ultima barra chiusa: ingresso alla prossima apertura (stima = chiusura)
            P = c[t]
            dist = K_STOP * atr[t]
            out.append(dict(asset=None, side="long" if dr > 0 else "short", dr=dr, sig_t=ts[t], entry_t=ts[t] + BAR, entry=P,
                            stop=P - dr * dist, target=P + dr * TGT_R * dist, d=dist / P, exit="pending", exit_t=None,
                            exit_px=None, R=None, net=None, a10=None, liq=False, bars=0, est=True))
            break
        P = o[e]
        dist = K_STOP * atr[t]
        S, T = P - dr * dist, P + dr * TGT_R * dist
        reason, j, px, worst = "open", None, None, P
        for k in range(e, min(e + HOLD, n)):
            hi, lo = (h[k], l[k]) if dr > 0 else (-l[k], -h[k])
            worst = min(worst, lo) if dr > 0 else max(worst, -lo)
            if lo <= dr * S:                      # stop prima del target nella stessa barra
                reason, j, px = "stop", k, (min(S, o[k]) if dr > 0 else max(S, o[k]))
                break
            if hi >= dr * T:
                reason, j, px = "tgt", k, T
                break
            if k == e + HOLD - 1 and k < nc:      # uscita a tempo solo su barra chiusa
                reason, j, px = "time", k, c[k]
        tr = dict(asset=None, side="long" if dr > 0 else "short", dr=dr, sig_t=ts[t], entry_t=ts[e], entry=P, stop=S, target=T,
                  d=dist / P, liq=False, est=False)
        if reason == "open":
            last = c[n - 1]
            g = dr * (last - P) / P
            tr.update(exit="open", exit_t=None, exit_px=None, R=None, net=None, a10=None, bars=n - e, last=last,
                      R_open=(g - FEE_IN - FEE_OUT) / (dist / P), time_exit_t=ts[e] + HOLD * BAR)
            out.append(tr)
            break
        gross = dr * (px - P) / P
        net = gross - FEE_IN - (FEE_STOP if reason == "stop" else FEE_OUT)
        mae = dr * (P - worst) / P
        liq = bool((tr["d"] >= LIQ and mae >= LIQ) or gross <= -LIQ)
        tr.update(exit=reason, exit_t=ts[j] + BAR, exit_px=px, R=net / tr["d"], net=net, liq=liq,
                  a10=-1.0 if liq else max(MAX_LEV * net, -1.0), bars=j - e + 1)
        out.append(tr)
        nxt = j + 1
    return out


def closed(trs: list[dict]) -> list[dict]:
    return [t for t in trs if t["exit"] not in ("open", "pending")]


def stats(trs: list[dict]) -> dict:
    R = np.array([t["R"] for t in closed(trs)])
    if not len(R):
        return dict(n=0)
    gw, gl = R[R > 0].sum(), -R[R < 0].sum()
    return dict(n=int(len(R)), wr=round(float((R > 0).mean()) * 100, 1), meanR=round(float(R.mean()), 3), sumR=round(float(R.sum()), 2),
                pf=round(float(gw / gl), 2) if gl > 0 else None, nliq=int(sum(t["liq"] for t in closed(trs))),
                p_d95=round(float(np.mean([t["d"] >= LIQ for t in closed(trs)])) * 100, 1))


def simulate(trs: list[dict], capital: float = 200.0, risk: float = 0.01, start: str = START, mode: str = "risk",
             max_open: float = 3.0) -> dict:
    """Conto composto sui trade chiusi (stessa logica della dashboard). mode 'risk': size = rischio/distanza stop limitata a
    10x, con più asset rischio aperto totale <= max_open x rischio e nozionale aperto <= 10x l'equity; mode 'x10': tutto il
    capitale a 10x, un trade alla volta (i trade che si sovrappongono a uno aperto si saltano)."""
    t0 = pd.Timestamp(start)
    T = sorted([t for t in closed(trs) if t["entry_t"] >= t0], key=lambda t: (t["entry_t"], t["asset"] or ""))
    ev = sorted([(t["entry_t"], 1, i) for i, t in enumerate(T)] + [(t["exit_t"], 0, i) for i, t in enumerate(T)])
    eq, pk, dd, opn, n, wins, Rs = capital, capital, 0.0, {}, 0, 0, []
    busy_until = None
    for when, kind, i in ev:
        t = T[i]
        if kind == 1:
            if mode == "x10":
                if eq <= 0 or (busy_until is not None and t["entry_t"] < busy_until):
                    continue
                opn[i] = eq
                busy_until = t["exit_t"]
                continue
            r_open = sum(x[1] for x in opn.values())
            nz_open = sum(x[0] for x in opn.values())
            if eq <= 0 or r_open + risk > max_open * risk + 1e-12:
                continue
            nz = min(eq * risk / t["d"], MAX_LEV * eq - nz_open)
            if nz <= 0:
                continue
            opn[i] = (nz, risk)
        elif i in opn:
            if mode == "x10":
                eq = opn.pop(i) * (1 + t["a10"])
            else:
                eq += opn.pop(i)[0] * t["net"]
            n += 1
            wins += t["R"] > 0
            Rs.append(t["R"])
            pk = max(pk, eq)
            dd = min(dd, eq / pk - 1 if pk > 0 else -1.0)
    eq, dd = float(eq), float(dd)
    return dict(final=round(eq, 2), ret=round((eq / capital - 1) * 100, 1), dd=round(dd * 100, 1), n=n,
                wr=round(float(wins) / n * 100, 1) if n else None, meanR=round(float(np.mean(Rs)), 3) if Rs else None,
                bust=bool(eq < capital * 0.01))


# ---------------------------------------------------------------------------------------------------------- dashboard
def _r(x, p=6):
    return None if x is None or (isinstance(x, float) and not np.isfinite(x)) else float(f"{x:.{p}g}")


def _s(t) -> int:
    return int(pd.Timestamp(t).timestamp())


def asset_view(asset: str, d: pd.DataFrame, live: pd.DataFrame, trs: list[dict]) -> dict:
    """Dati compatti per la dashboard: ultime CHART_BARS candele (+ barra in corso) con Ichimoku, nube proiettata 26 barre
    avanti, trade (tutti dal 2021, campi corti) e stato attuale."""
    full = pd.concat([d, live]) if len(live) else d
    ind = indicators(full)
    w, iw = full.iloc[-CHART_BARS:], ind.iloc[-CHART_BARS:]
    fut_t = [full.index[-1] + BAR * (k + 1) for k in range(26)]
    ser = dict(t=[_s(x) for x in w.index], o=[_r(x) for x in w.open], h=[_r(x) for x in w.high], l=[_r(x) for x in w.low],
               c=[_r(x) for x in w.close], ten=[_r(x) for x in iw.ten], kij=[_r(x) for x in iw.kij],
               sa=[_r(x) for x in iw.sa] + [_r(x) for x in ind.sa_raw.iloc[-26:]],
               sb=[_r(x) for x in iw.sb] + [_r(x) for x in ind.sb_raw.iloc[-26:]], ft=[_s(x) for x in fut_t],
               live=bool(len(live)))
    code = {"tgt": "T", "stop": "S", "time": "H", "open": "O", "pending": "P"}
    tl = [[_s(t["sig_t"]), _s(t["entry_t"]), _s(t["exit_t"]) if t["exit_t"] is not None else None, t["dr"], _r(t["entry"]),
           _r(t["exit_px"]) if t["exit_px"] is not None else None, _r(t["stop"]), _r(t["target"]), code[t["exit"]],
           _r(t["R"], 4) if t["R"] is not None else None, _r(t["net"], 5) if t["net"] is not None else None, _r(t["d"], 4),
           int(t["liq"])] for t in trs]
    last = trs[-1] if trs and trs[-1]["exit"] in ("open", "pending") else None
    sig = signals(d)
    li = np.flatnonzero(sig)
    st = dict(price=_r(full.close.iloc[-1]), bar_t=_s(d.index[-1]), last_signal=None, pos=None)
    if len(li):
        k = li[-1]
        st["last_signal"] = dict(t=_s(d.index[k]), side="long" if sig[k] > 0 else "short", px=_r(d.close.iloc[k]))
    if last:
        st["pos"] = dict(status=last["exit"], side=last["side"], entry=_r(last["entry"]), entry_t=_s(last["entry_t"]),
                         stop=_r(last["stop"]), target=_r(last["target"]), d=_r(last["d"], 4), est=last["est"],
                         R_open=_r(last.get("R_open"), 3), time_exit_t=_s(last["time_exit_t"]) if last.get("time_exit_t") else None)
    oos = stats([t for t in trs if t["entry_t"] >= pd.Timestamp("2024-01-01")])
    return dict(series=ser, trades=tl, state=st, stats=stats(trs), oos=oos)


# ------------------------------------------------------------------------------------------------------------ eventi
def _p(x: float) -> str:
    x = float(x)
    s = f"{x:,.2f}" if x >= 100 else f"{x:,.4f}" if x >= 1 else f"{x:.5f}"
    return "$" + s.replace(",", "X").replace(".", ",").replace("X", ".")


def _when(ts) -> str:
    return pd.Timestamp(ts).strftime("%d/%m %H:%M UTC")


def _n(x: float, d: int = 2, sign: bool = False) -> str:
    """Numero all'italiana: 1.234,56 (segno esplicito se sign)."""
    s = f"{abs(x):,.{d}f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return ("−" if x < 0 else "+" if sign and x > 0 else "") + s


def _pc(x: float, d: int = 2) -> str:
    return f"{x:.{d}f}".replace(".", ",") + "%"


def sizing(d: float, capital: float, risk: float) -> dict:
    nz = capital * risk / d
    lev = nz / capital
    return dict(risk_eur=capital * risk, notional=min(nz, capital * MAX_LEV), lev=lev, capped=lev > MAX_LEV)


def format_signal(a: str, t: dict, capital: float) -> str:
    L = t["side"] == "long"
    lines = [f"<b>RADAR · INTRADAY {a}/USDT 4h · NUOVO SEGNALE {'🟢 LONG' if L else '🔴 SHORT'}</b>",
             f"Ichimoku: Tenkan incrocia {'sopra' if L else 'sotto'} la Kijun con prezzo {'sopra' if L else 'sotto'} la nube "
             f"(chiusura {_when(t['sig_t'] + BAR)})",
             f"<b>Ingresso</b> {'~' if t['est'] else ''}{_p(t['entry'])} {'(stima: apertura della prossima candela 4h)' if t['est'] else '(apertura della candela 4h)'}",
             f"<b>Stop</b> {_p(t['stop'])} (2 ATR, −{_pc(t['d'] * 100)}) · <b>Target</b> {_p(t['target'])} (3R)",
             f"<b>Uscita a tempo</b> {_when(t['entry_t'] + HOLD * BAR)} (48 candele 4h = 8 giorni)", ""]
    for r in (0.01, 0.02):
        s = sizing(t["d"], capital, r)
        lines.append(f"Rischio {int(r * 100)}% su {_n(capital, 0)} €: perdita allo stop {_n(s['risk_eur'], 2)} € · posizione "
                     f"{_n(s['notional'], 0)} € · leva {_n(s['lev'], 2)}x" + (" (oltre 10x: posizione limitata a 10x)" if s["capped"] else ""))
    if t["d"] >= LIQ:
        lines.append(f"⚠️ Stop al {_pc(t['d'] * 100, 1)}: a 10x verresti liquidato prima dello stop (liquidazione ~9,5%). Usa leva più bassa.")
    lines.append("Segnali sullo spot Binance (il perp segue entro pochi decimi di %). Strategia su carta, non validata con trade reali.")
    return "\n".join(lines)


def format_exit(a: str, t: dict) -> str:
    head = {"tgt": "🎯 TARGET RAGGIUNTO", "stop": "🛑 STOP", "time": "⏱ USCITA A TEMPO"}[t["exit"]]
    return (f"<b>RADAR · INTRADAY {a}/USDT 4h · {head}</b>\n"
            f"{'Long' if t['dr'] > 0 else 'Short'} da {_p(t['entry'])} ({_when(t['entry_t'])}) → {_p(t['exit_px'])} ({_when(t['exit_t'])})\n"
            f"Risultato {_n(t['R'], 2, True)}R · {_n(t['net'] * 100, 2, True)}% sul prezzo, costi stimati inclusi. "
            + ("Chiudi la posizione a mercato." if t["exit"] == "time" else "Se l'ordine era piazzato, la posizione è chiusa."))


def diff_events(trades: dict[str, list[dict]], st: dict | None, now: pd.Timestamp | None = None,
                capital: float = 200.0) -> tuple[list[str], dict]:
    """Messaggi Telegram con dedupe (state.json, chiave 'intra'). Al primo giro registra lo storico senza inviare nulla."""
    now = now or pd.Timestamp.utcnow().tz_localize(None)
    first = st is None
    st = dict(st or {})
    seen, msgs = set(st.get("seen", [])), []
    for a, trs in trades.items():
        for t in trs:
            ks = f"{a}:sig:{_s(t['sig_t'])}"
            if ks not in seen:
                seen.add(ks)
                if not first and t["exit"] in ("open", "pending") and now - t["sig_t"] < 3 * BAR:
                    msgs.append(format_signal(a, t, capital))
            if t["exit"] in ("tgt", "stop", "time"):
                kx = f"{a}:exit:{_s(t['sig_t'])}"
                if kx not in seen:
                    seen.add(kx)
                    if not first and now - t["exit_t"] < pd.Timedelta(days=2):
                        msgs.append(format_exit(a, t))
    st["seen"] = sorted(seen)[-3000:] if len(seen) > 3000 else sorted(seen)
    return msgs, st


# ------------------------------------------------------------------------------------------------------------- giro
def evaluate(fetch: bool = True) -> tuple[dict, dict[str, list[dict]]]:
    """Aggiorna i dati, calcola trade e stato per i 10 asset. Ritorna (report compatto per la dashboard, trade per asset)."""
    rep, all_tr = dict(assets={}, start=START, rule=dict(k=K_STOP, tgt=TGT_R, hold=HOLD, fee_side=FEE_IN, fee_stop=FEE_STOP,
                                                           liq=LIQ, max_lev=MAX_LEV)), {}
    for a in ASSETS:
        try:
            d, live = update(a) if fetch else (load(a), pd.DataFrame())
        except Exception as e:  # noqa: BLE001
            print(f"[intra] {a}: dati non aggiornati ({type(e).__name__}), uso la cache")
            d, live = load(a), pd.DataFrame()
        if len(d) < 80:
            continue
        trs = backtest(d, live)
        for t in trs:
            t["asset"] = a
        all_tr[a] = trs
        rep["assets"][a] = asset_view(a, d, live, trs)
    flat = [t for v in all_tr.values() for t in v]
    cap = float(os.environ.get("RADAR_INTRA_CAPITAL", "200"))
    rep["capital"] = cap
    rep["summary"] = dict(
        all=stats(flat), oos=stats([t for t in flat if t["entry_t"] >= pd.Timestamp("2024-01-01")]),
        basket={f"r{int(r * 100)}": simulate(flat, cap, r) for r in (0.01, 0.02)} | {"x10": simulate(flat, cap, mode="x10")},
        per_asset={a: {f"r{int(r * 100)}": simulate(v, cap, r) for r in (0.01, 0.02)} | {"x10": simulate(v, cap, mode="x10")}
                   for a, v in all_tr.items()})
    rep["updated"] = str(pd.Timestamp.utcnow().tz_localize(None).floor("min"))
    return rep, all_tr


if __name__ == "__main__":
    import json
    r, _ = evaluate()
    print(json.dumps(r["summary"], indent=1))
