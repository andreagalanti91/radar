"""Ingressi/uscite a scaglioni · motore di ricerca (fase 1, 22/11/2026).

Copia di radar.weekly.simulate (W3.1) con la posizione divisa in LOTTI (scaglioni), ciascuno con quantità, costo, distanza di
trailing k e stop propri. A configurazione predefinita (E0 U0 T0 k 2,5 D0 G0) riproduce radar.weekly al centesimo
(controllo in __main__ e in iu_count.py). Non modifica radar/. Dati congelati di research/p2_nuovi (fino al 15/11/2026).

Configurazione `cfg` (dict, chiavi facoltative):
- k:      distanza in ATRw di stop iniziale e trailing (W3.1: 2,5); la dimensione usa lo stesso k (rischio allo stop R = 10%).
- entry:  ("E0",) tutto all'apertura dopo la decisione;
          ("E1", offsets) DCA a tempo: parti uguali alle aperture dei giorni entry+offset (3 parti: (0, 2, 4) = lun/mer/ven);
          ("E2", n) DCA settimanale: 1/n all'apertura dopo la decisione e 1/n dopo ciascuna delle n−1 decisioni successive in cui
                il segnale d'ingresso dello stesso lato è ancora vero (altrimenti quello scaglione si salta, senza recupero);
          ("E3", m, days) 1/2 all'apertura, 1/2 con limite a prezzo d'ingresso − lato·m·ATRw(segnale) per `days` giorni
                (giorno d'ingresso compreso); se non eseguito, a mercato all'apertura del giorno successivo alla finestra.
- exit:   ("U0",) tutto insieme; ("U1", a) frazione a alla prima condizione d'uscita settimanale (EMA21/distribuzione), il resto
          alla decisione successiva se una condizione d'uscita è ancora vera (altrimenti il resto continua e la prossima
          condizione lo chiude tutto); stop e trailing chiudono sempre tutto;
          ("U2", k1, k2) due lotti uguali con stop iniziale e trailing a k1 e k2 ATRw (dimensione calcolata con k = (k1+k2)/2).
- tp:     None oppure dict(levels=(3,), frac=1/3): presa di frac della quantità iniziale con limite a ingresso ± m·R
          (R = k·ATRw del segnale), riempita al livello o all'apertura se il prezzo apre oltre; il giorno dello stop vale lo stop.
- dist:   ("D0",) attuale; ("D1",) nessuna uscita per distribuzione; ("D2", n) condizione vera per n decisioni consecutive;
          ("D3", s) soglie di funding moltiplicate per s (FUND_HOT·s, FUND_COLD·s).
- anchor: giorno della candela settimanale ("SUN" = W3.1); simulate_g7() = 7 sotto-portafogli da 1/7, uno per giorno.

Dimensione: ogni scaglione j ha esposizione w_j · min(1, R·ref_j / |ref_j − stop_j|) · equity al primo ingresso, con ref_1 =
chiusura del segnale e stop_1 = stop iniziale (identico a W3.1), ref_j = chiusura del giorno prima (o prezzo limite) e stop_j =
stop in vigore per gli scaglioni successivi; esposizione totale mai oltre 1x dell'equity corrente.
Ordine nel giorno: ordini all'apertura (uscite, ingressi, scaglioni a tempo) → limite d'ingresso E3 (eseguito prima dello stop:
ipotesi prudente) → stop per lotto (prima dello stop, mai TP lo stesso giorno) → TP → funding → equity → decisione settimanale.
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402

DAYS = ["MON", "TUE", "WED", "THU", "FRI", "SAT", "SUN"]
R = W.R_LONG
assert W.R_LONG == W.R_SHORT == 0.10 and W.STOP_K == 2.5


def weekly_bars(f: pd.DataFrame, anchor: str = "SUN") -> pd.DataFrame:
    """Come radar.weekly.weekly_bars con il giorno di chiusura come parametro (copia di research/notte_1511/n1/run.py)."""
    if anchor == "SUN":
        return W.weekly_bars(f)
    rule = f"W-{anchor}"
    w = f[["open", "high", "low", "close"]].resample(rule).agg({"open": "first", "high": "max", "low": "min", "close": "last"})
    w["flow"] = W.live_flow(f).resample(rule).last()
    w["fund7"] = f["funding"].fillna(0).rolling(7).mean().resample(rule).last()
    c = w["close"]
    w["sma"] = c.rolling(W.SMA).mean()
    w["ema20"] = c.ewm(span=W.EMA_T, adjust=False).mean()
    w["ema21"] = c.ewm(span=W.EMA_X, adjust=False).mean()
    tr = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
    w["atr"] = tr.ewm(alpha=1 / W.ATR_N, adjust=False).mean()
    up = (c > w["sma"]) & (w["ema20"] > w["ema20"].shift(1))
    dn = (c < w["sma"]) & (w["sma"] < w["sma"].shift(4)) & (w["ema20"] < w["ema20"].shift(1))
    above = (c > w["sma"]).astype(int)
    w["trend_age"] = above.groupby((above == 0).cumsum()).cumsum()
    m = c.ewm(span=W.MACD_P[0], adjust=False).mean() - c.ewm(span=W.MACD_P[1], adjust=False).mean()
    w["macd"], w["macd_sig"] = m, m.ewm(span=W.MACD_P[2], adjust=False).mean()
    w["f1_ok"] = (w["trend_age"] < W.OLD_TREND) | ((w["macd"] > w["macd_sig"]) & (w["macd"] > 0))
    w["long"] = (up & (c > w["ema21"]) & (w["flow"] > 0) & w["f1_ok"]).fillna(False)
    w["short"] = (dn & (c < w["ema21"]) & (w["flow"] < 0)).fillna(False)
    w["dist_long"] = ((w["fund7"] > W.FUND_HOT) & (w["flow"] < 0)).fillna(False)
    w["dist_short"] = ((w["fund7"] < W.FUND_COLD) & (w["flow"] > 0)).fillna(False)
    return w[w.index <= f.index[-1]]


def dist_flags(w: pd.DataFrame, dist: tuple) -> tuple[pd.Series, pd.Series]:
    """Condizione di distribuzione per long e short secondo la variante D."""
    kind = dist[0]
    if kind == "D1":
        z = pd.Series(False, index=w.index)
        return z, z
    hot, cold = W.FUND_HOT, W.FUND_COLD
    if kind == "D3":
        hot, cold = hot * dist[1], cold * dist[1]
    dl = ((w["fund7"] > hot) & (w["flow"] < 0)).fillna(False)
    ds = ((w["fund7"] < cold) & (w["flow"] > 0)).fillna(False)
    if kind == "D2":
        n = dist[1]
        dl = dl.astype(int).rolling(n, min_periods=n).sum().eq(n)
        ds = ds.astype(int).rolling(n, min_periods=n).sum().eq(n)
    return dl, ds


def simulate(f: pd.DataFrame, cfg: dict | None = None, start: str = W.START, end: str | None = None,
             capital: float = 10000.0, wb: pd.DataFrame | None = None) -> dict:
    cfg = cfg or {}
    k = cfg.get("k", W.STOP_K)
    entry = cfg.get("entry", ("E0",))
    exitm = cfg.get("exit", ("U0",))
    tp = cfg.get("tp")
    dist = cfg.get("dist", ("D0",))
    anchor = cfg.get("anchor", "SUN")
    dow = DAYS.index(anchor)
    f = f[f["close"].notna()]
    if end is not None:
        f = f[f.index <= end]
    w = weekly_bars(f, anchor) if wb is None else wb[wb.index <= f.index[-1]]
    DL, DS = dist_flags(w, dist)
    idx = f.index
    O, H, L, C = (f[c].to_numpy(float) for c in ("open", "high", "low", "close"))
    FU = f["funding"].fillna(0).to_numpy(float)
    t0 = idx.searchsorted(pd.Timestamp(start))
    cash, side, pend, tr = 1.0, 0, [], None
    lots: list[dict] = []
    trades, events, eq = [], [], np.full(len(idx), np.nan)
    ex = np.zeros(len(idx))
    st: dict = {}
    k_lots = (exitm[1], exitm[2]) if exitm[0] == "U2" else (k,)
    k_size = float(np.mean(k_lots))

    def fee() -> float:
        return W.FEE_SPOT if side > 0 else W.FEE_PERP

    def qtot() -> float:
        return sum(l["q"] for l in lots)

    def ev(i, kind, **x):
        events.append(dict(day=str(idx[i].date()), kind=kind, side=side, signal=tr["signal"] if tr else None, **x))

    def buy(px: float, expo: float, i: int, kind: str, kk: tuple) -> None:
        """Compra esposizione `expo` (× equity al primo ingresso) divisa in parti uguali sui lotti con trailing kk."""
        nonlocal cash
        e_now = cash + sum(l["q"] * px - l["cost"] for l in lots)
        room = max(0.0, e_now - sum(abs(l["q"]) * px for l in lots))
        notional = min(expo * st["eq_sig"], room)
        if notional <= 0:
            return
        for kj in kk:
            q = side * notional / len(kk) / px
            same = [l for l in lots if l["k"] == kj]
            stop = same[0]["stop"] if same else float(tr["sig_close"] - side * kj * tr["atr"])
            lots.append(dict(q=q, cost=q * px, k=kj, stop=stop, stop0=float(tr["sig_close"] - side * kj * tr["atr"])))
            cash -= abs(q) * px * fee()
        st["n_fills"] += 1
        ev(i, kind, expo=round(notional / st["eq_sig"], 4))

    def sell_frac(p: float, px: float, sel=None) -> None:
        nonlocal cash
        for l in (sel if sel is not None else lots):
            cash += p * (l["q"] * px - l["cost"]) - abs(p * l["q"]) * px * fee()
            l["q"] *= (1 - p)
            l["cost"] *= (1 - p)

    def finish(i: int, px: float, reason: str) -> None:
        nonlocal side, tr, lots
        tr.update(exit=str(idx[i].date()), exit_px=round(px, 2), reason=reason, pnl=cash / tr["eq0"] - 1,
                  move=(px / tr["entry_px"] - 1) * side, n_fills=st["n_fills"], partial=st["partial"], tp_done=st["tp_done"])
        trades.append(tr)
        tr, side, lots = None, 0, []

    def close_all(px: float, i: int, reason: str) -> None:
        sell_frac(1.0, px)
        finish(i, px, reason)

    def ref_stop() -> float:
        s = [l["stop"] for l in lots if l["k"] == k_lots[0]]
        return s[0] if s else float(tr["sig_close"] - side * k_lots[0] * tr["atr"])

    def tranche_expo(wj: float, ref: float) -> float:
        d = abs(ref - ref_stop())
        if (ref - ref_stop()) * side <= 0:
            return 0.0
        return wj * min(1.0, R * ref / d)

    for i in range(t0, len(idx)):
        day = idx[i]
        todo, pend = pend, []
        for a in todo:                                  # ordini all'apertura decisi alla chiusura di ieri
            if a[0] == "exit" and side:
                close_all(O[i] * (1 - W.SLIP * side), i, a[1])
            elif a[0] == "partial" and side and a[1] >= 1 - 1e-12:
                close_all(O[i] * (1 - W.SLIP * side), i, a[2])
            elif a[0] == "partial" and side:
                sell_frac(a[1], O[i] * (1 - W.SLIP * side))
                st["partial"] += 1
                ev(i, "partial_exit", frac=a[1])
            elif a[0] == "enter" and not side:
                side, wk, dday = a[1], a[2], a[3]
                px = O[i] * (1 + W.SLIP * side)
                tr = dict(signal=str(dday.date()), entry=str(day.date()), side="long" if side > 0 else "short",
                          entry_px=round(px, 2), sig_close=float(wk["close"]), atr=float(wk["atr"]), eq0=cash,
                          stop0=float(wk["close"] - side * k_lots[0] * wk["atr"]), best=O[i], curatr=float(wk["atr"]))
                tr["rdist"] = k * float(wk["atr"])
                st = dict(eq_sig=cash, n_fills=0, partial=0, tp_done=0, i0=i, e2_left=0, e3_open=False, u1=False)
                full = min(1.0, R / (k_size * wk["atr"] / wk["close"]))
                if entry[0] == "E0":
                    buy(px, full, i, "enter", k_lots)
                elif entry[0] == "E1":
                    st["e1"] = [i + o for o in entry[1]]
                    st["e1_w"] = 1.0 / len(entry[1])
                    buy(px, full * st["e1_w"], i, "enter", k_lots)
                    st["e1"] = st["e1"][1:]
                elif entry[0] == "E2":
                    st["e2_left"], st["e2_w"] = entry[1] - 1, 1.0 / entry[1]
                    buy(px, full * st["e2_w"], i, "enter", k_lots)
                elif entry[0] == "E3":
                    buy(px, full * 0.5, i, "enter", k_lots)
                    st["e3_open"], st["e3_lim"] = True, px / (1 + W.SLIP * side) - side * entry[1] * tr["atr"]
                    st["e3_end"] = i + entry[2] - 1
                tr["expo"] = round(sum(abs(l["q"]) for l in lots) * px / st["eq_sig"], 4)
                tr["q0"] = abs(qtot())
            elif a[0] == "add" and side:
                buy(O[i] * (1 + W.SLIP * side), a[1], i, a[2], k_lots)
        if side and entry[0] == "E1" and st.get("e1") and st["e1"][0] == i:     # scaglione a tempo all'apertura
            buy(O[i] * (1 + W.SLIP * side), tranche_expo(st["e1_w"], C[i - 1]), i, "e1_add", k_lots)
            st["e1"] = st["e1"][1:]
        if side:
            for l in lots:                               # trailing a cricchetto per lotto
                tl = tr["best"] - side * l["k"] * tr["curatr"]
                l["stop"] = max(l["stop"], tl) if side > 0 else min(l["stop"], tl)
            if st["e3_open"] and i <= st["e3_end"]:     # limite E3 (prima dello stop: prudente)
                lim = st["e3_lim"]
                if (side > 0 and L[i] <= lim) or (side < 0 and H[i] >= lim):
                    fill = (min(O[i], lim) if side > 0 else max(O[i], lim)) * (1 + W.SLIP * side)
                    buy(fill, tranche_expo(0.5, lim), i, "e3_limit", k_lots)
                    st["e3_open"] = False
            hits = [l for l in lots if (side > 0 and L[i] <= l["stop"]) or (side < 0 and H[i] >= l["stop"])]
            while tp and not hits and st["tp_done"] < len(tp["levels"]):
                lvl = tr["entry_px"] + side * tp["levels"][st["tp_done"]] * tr["rdist"]
                if not ((side > 0 and H[i] >= lvl) or (side < 0 and L[i] <= lvl)):
                    break
                fillp = (max(O[i], lvl) if side > 0 else min(O[i], lvl)) * (1 - W.SLIP * side)
                p = min(tp["frac"] * tr["q0"], abs(qtot())) / abs(qtot())
                sell_frac(p, fillp)
                st["tp_done"] += 1
                ev(i, "tp", level=tp["levels"][st["tp_done"] - 1])
            last_px, last_reason = None, None
            for l in hits:
                px = (min(O[i], l["stop"]) if side > 0 else max(O[i], l["stop"])) * (1 - W.SLIP * side)
                sell_frac(1.0, px, [l])
                l["dead"] = True
                last_px, last_reason = px, ("stop" if l["stop"] == l["stop0"] else "trail")
            if hits:
                lots = [l for l in lots if not l.get("dead")]
                if not lots:
                    finish(i, last_px, last_reason)
                else:
                    ev(i, "lot_stop", reason=last_reason)
            if side:
                cash -= (1.0 if side < 0 else 0.0) * qtot() * C[i] * FU[i]
                tr["best"] = max(tr["best"], C[i]) if side > 0 else min(tr["best"], C[i])
                if st["e3_open"] and i == st["e3_end"]:            # finestra scaduta: a mercato all'apertura di domani
                    st["e3_open"] = False
                    pend.append(("add", tranche_expo(0.5, C[i]), "e3_market"))
        pos = sum(l["q"] * C[i] - l["cost"] for l in lots) if side else 0.0
        eq[i] = cash + pos
        ex[i] = abs(qtot() * C[i]) / eq[i] if side else 0.0
        if day.dayofweek == dow and day in w.index:
            wk = w.loc[day]
            if side:
                tr["curatr"] = float(wk["atr"])
                beyond = wk["close"] < wk["ema21"] if side > 0 else wk["close"] > wk["ema21"]
                dd = bool(DL.loc[day] if side > 0 else DS.loc[day])
                reason = "ema" if beyond else ("dist" if dd else None)
                if reason:
                    pend = [a for a in pend if a[0] != "add"]
                    st["e3_open"], st["e2_left"], st["e1"] = False, 0, []
                    if exitm[0] == "U1" and not st["u1"]:
                        st["u1"] = True
                        pend.append(("partial", exitm[1], reason))
                        ev(i, "u1_first", reason=reason)
                    else:
                        pend.append(("exit", reason))
                else:
                    if st["u1"]:
                        ev(i, "u1_unconfirmed")
                    if st["e2_left"] > 0:
                        st["e2_left"] -= 1
                        if wk["long"] if side > 0 else wk["short"]:
                            pend.append(("add", tranche_expo(st["e2_w"], float(wk["close"])), "e2_add"))
                        else:
                            ev(i, "e2_skip")
            else:
                if wk["long"]:
                    pend.append(("enter", 1, wk, day))
                elif wk["short"]:
                    pend.append(("enter", -1, wk, day))
    out = {"trades": trades, "events": events, "equity": pd.Series(eq[t0:], idx[t0:]) * capital,
           "expo": pd.Series(ex[t0:], idx[t0:]), "open": None, "weekly": w}
    if side:
        i = len(idx) - 1
        out["open"] = dict(tr, last=float(C[i]), move=(C[i] / tr["entry_px"] - 1) * side, pnl=eq[i] / tr["eq0"] - 1,
                           pnl_close=(eq[i] - abs(qtot()) * C[i] * fee()) / tr["eq0"] - 1, n_fills=st["n_fills"],
                           partial=st["partial"], tp_done=st["tp_done"])
    return out


def simulate_g7(f: pd.DataFrame, cfg: dict | None = None, start: str = W.START, end: str | None = None,
                capital: float = 10000.0) -> dict:
    """G7: 7 sotto-portafogli da capital/7, uno per giorno di chiusura settimanale, mai ribilanciati."""
    runs = {d: simulate(f, dict(cfg or {}, anchor=d), start=start, end=end, capital=capital / 7) for d in DAYS}
    eq = sum(r["equity"] for r in runs.values())
    trades = [dict(t, anchor=d) for d, r in runs.items() for t in r["trades"]]
    opens = [dict(r["open"], anchor=d) for d, r in runs.items() if r["open"]]
    return {"trades": trades, "events": [e for r in runs.values() for e in r["events"]], "equity": eq,
            "open_list": opens, "open": None, "runs": runs}


if __name__ == "__main__":
    sys.path.insert(0, str(ROOT / "research" / "p2_nuovi"))
    from p2_data import load
    d = load()
    for x, s, e in ((d["f"], W.START, None), (d["fl"], "2018-01-01", "2020-12-31")):
        xx = x if e is None else x[x.index <= e]
        a, b = W.simulate(xx, start=s), simulate(x, start=s, end=e)
        print(s, "uguale a radar.weekly:", np.allclose(a["equity"].to_numpy(), b["equity"].to_numpy(), rtol=0, atol=1e-6),
              len(a["trades"]) == len(b["trades"]), round(float(b["equity"].iloc[-1])))
