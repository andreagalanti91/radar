"""MACD weekly flip (CM_Ult_MacD_MTF 12/26/9) long+short — BTC, ETH, SOL dal 2021-01-01.

Uso:  python research/macd_flip/fetch.py      (una volta: cache klines 1d Binance spot)
      python research/macd_flip/backtest.py   (stampa tabelle, scrive trades_<ASSET>.csv e results.csv)

Barre settimanali come TradingView "1W": lunedì 00:00 UTC open -> domenica close (da klines 1d).
Segnale sulla chiusura settimanale; fill all'open del lunedì successivo (default) o alla close del segnale.
Costi 0,1% per lato; funding perp sugli short = 0 (gli short di norma RICEVONO funding positivo: ipotesi
conservativa). 1x, capitale pieno, compounding per trade, 10.000 $ al 2021-01-01, si parte flat.
Equity mark-to-market giornaliera (close 1d) -> max DD giornaliero.

Regole preregistrate (stesse su tutti gli asset, nessun tuning per asset):
 R1  flip puro: long su cross_UP, short su cross_DN, sempre a mercato
 R2  R1 + filtro EMA50: long solo se close>EMA50, short solo se close<EMA50, altrimenti flat
 R3a cross "alert" TV: long su UP con macd>0, short su DN con macd<0; uscita su cross opposto
 R3b cross di inversione: long su UP con macd<0, short su DN con macd>0; uscita su cross opposto
 R4a R1 + stop all'estremo della settimana del segnale (long: min, short: max); dopo lo stop flat
 R4b R1 + stop 2xATR14 settimanale dal prezzo d'ingresso
 R5  R1 solo long (flat su cross_DN)
 R6  R1 + filtro regime close vs SMA200 settimanale (se SMA200 non disponibile -> EMA50)
 R7  ingressi R1; uscita su cross opposto OPPURE close settimanale oltre EMA20 (long: close<EMA20,
     short: close>EMA20), poi flat fino al cross successivo (aggiunta su contesto screenshot utente)
"""
import os, sys
import numpy as np, pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
DATA = os.path.join(HERE, "data")
START = pd.Timestamp("2021-01-01")
COST = 0.001
CAP0 = 10_000.0
ASSETS = {"BTC": "BTCUSDT", "ETH": "ETHUSDT", "SOL": "SOLUSDT"}
RULES = ["R1", "R2", "R3a", "R3b", "R4a", "R4b", "R5", "R6", "R7"]


def ema(s, n):
    return s.ewm(span=n, adjust=False).mean()


def load(sym, today=None):
    d = pd.read_csv(os.path.join(DATA, f"{sym}_1d.csv"), parse_dates=["date"]).set_index("date")
    d = d.iloc[:-1]  # ultima candela 1d è in corso
    return d


def weekly(d, fast=12, slow=26, sig=9):
    w = d.resample("W-MON", label="left", closed="left").agg(
        dict(open="first", high="max", low="min", close="last"))
    w = w[w.index + pd.Timedelta(days=6) <= d.index[-1]]  # solo settimane complete
    w["macd"] = ema(w.close, fast) - ema(w.close, slow)
    w["sig"] = ema(w.macd, sig)
    w["e20"], w["e50"] = ema(w.close, 20), ema(w.close, 50)
    w["sma200"] = w.close.rolling(200).mean()
    tr = pd.concat([w.high - w.low, (w.high - w.close.shift()).abs(), (w.low - w.close.shift()).abs()], axis=1).max(axis=1)
    w["atr"] = tr.ewm(alpha=1 / 14, adjust=False).mean()
    m, s = w.macd, w.sig
    w["up"] = (m > s) & (m.shift() <= s.shift())
    w["dn"] = (m < s) & (m.shift() >= s.shift())
    w["close_date"] = w.index + pd.Timedelta(days=6)
    return w


def target(rule, r):
    """posizione desiderata dopo un cross (None = nessun cambio)."""
    up, dn = r.up, r.dn
    if not (up or dn):
        return None
    side = 1 if up else -1
    if rule in ("R1", "R4a", "R4b", "R7"):
        return side
    if rule == "R5":
        return 1 if up else 0
    if rule == "R2":
        ok = r.close > r.e50 if up else r.close < r.e50
        return side if ok else 0
    if rule == "R6":
        ref = r.sma200 if not np.isnan(r.sma200) else r.e50
        ok = r.close > ref if up else r.close < ref
        return side if ok else 0
    if rule == "R3a":
        return side if (r.macd > 0 if up else r.macd < 0) else 0
    if rule == "R3b":
        return side if (r.macd < 0 if up else r.macd > 0) else 0
    raise ValueError(rule)


def run(d, w, rule, start=START, end=None, fill="open"):
    end = end or d.index[-1]
    dd = d.loc[start:end]
    # ordini: giorno di esecuzione -> (target, stop)
    orders = {}
    for t, r in w[(w.close_date >= start) & (w.close_date <= end)].iterrows():
        tg = target(rule, r)
        if tg is None:
            continue
        stop = None
        if tg != 0 and rule == "R4a":
            stop = r.low if tg == 1 else r.high
        if tg != 0 and rule == "R4b":
            stop = ("atr", 2 * r.atr)
        day = r.close_date + pd.Timedelta(days=1) if fill == "open" else r.close_date
        orders[day] = (tg, stop, t)
    ema_exit = {}
    if rule == "R7":  # uscita EMA20 a chiusura settimanale -> esecuzione come gli altri ordini
        for t, r in w[(w.close_date >= start) & (w.close_date <= end)].iterrows():
            day = r.close_date + pd.Timedelta(days=1) if fill == "open" else r.close_date
            ema_exit[day] = -1 if r.close < r.e20 else (1 if r.close > r.e20 else 0)
    eq_base, pos, entry, stop, trades, cur = CAP0, 0, None, None, [], None
    eqs = []

    def close_trade(day, px, why):
        nonlocal eq_base, pos, cur
        g = max(0.0, 1 + pos * (px / cur["px_in"] - 1))
        eq_base = eq_base * (1 - COST) * g * (1 - COST)  # costo ingresso e uscita
        cur.update(uscita=day.date(), prezzo_uscita=round(px, 4), motivo=why,
                   pnl_pct=round(((1 - COST) ** 2 * g - 1) * 100, 2), capitale=round(eq_base))
        trades.append(cur); pos, cur = 0, None

    for day, b in dd.iterrows():
        o = orders.get(day)
        if fill == "open" and o is None and pos != 0 and ema_exit.get(day) == -pos:
            close_trade(day, b.open, "ema20")
        if o is not None and fill == "open":
            tg, st, sw = o
            if pos != 0 and tg != pos:
                close_trade(day, b.open, "cross")
            if tg != 0 and pos == 0:
                pos = tg
                cur = dict(segnale=(sw + pd.Timedelta(days=6)).date(), ingresso=day.date(),
                           lato="long" if tg == 1 else "short", prezzo_ingresso=round(b.open, 4))
                cur["px_in"] = b.open
                stop = (b.open - pos * st[1]) if isinstance(st, tuple) else st
        # liquidazione 1x short (prezzo raddoppia => capitale azzerato)
        if pos == -1 and b.high >= 2 * cur["px_in"]:
            close_trade(day, 2 * cur["px_in"], "liquidato")
        # stop intraday
        if pos != 0 and stop is not None:
            if pos == 1 and b.low <= stop:
                close_trade(day, min(b.open, stop), "stop")
            elif pos == -1 and b.high >= stop:
                close_trade(day, max(b.open, stop), "stop")
        if fill == "close" and o is None and pos != 0 and ema_exit.get(day) == -pos:
            close_trade(day, b.close, "ema20")
        if o is not None and fill == "close":
            tg, st, sw = o
            if pos != 0 and tg != pos:
                close_trade(day, b.close, "cross")
            if tg != 0 and pos == 0:
                pos = tg
                cur = dict(segnale=day.date(), ingresso=day.date(), lato="long" if tg == 1 else "short",
                           prezzo_ingresso=round(b.close, 4))
                cur["px_in"] = b.close
                stop = (b.close - pos * st[1]) if isinstance(st, tuple) else st
        mtm = eq_base if pos == 0 else eq_base * (1 - COST) * (1 + pos * (b.close / cur["px_in"] - 1))
        eqs.append((day, mtm, pos != 0))
    if pos != 0:
        b = dd.iloc[-1]
        close_trade(dd.index[-1], b.close, "aperto")
    eq = pd.DataFrame(eqs, columns=["date", "eq", "inmkt"]).set_index("date")
    tr = pd.DataFrame(trades)
    if len(tr):
        tr = tr.drop(columns="px_in")
    return eq, tr


def metrics(eq, tr):
    fin = eq["eq"].iloc[-1]
    yrs = (eq.index[-1] - eq.index[0]).days / 365.25
    cagr = (max(fin, 0) / CAP0) ** (1 / yrs) - 1
    mdd = (eq["eq"] / eq["eq"].cummax() - 1).min()
    out = dict(finale=round(fin), rend_pct=round((fin / CAP0 - 1) * 100, 1), cagr_pct=round(cagr * 100, 1),
               dd_pct=round(mdd * 100, 1), mar=round(cagr / abs(mdd), 2) if mdd < 0 else np.nan,
               trade=len(tr), tempo_mkt_pct=round(eq.inmkt.mean() * 100))
    if len(tr):
        r = tr.pnl_pct / 100
        out.update(wr_pct=round((r > 0).mean() * 100), avg_win=round(r[r > 0].mean() * 100, 1) if (r > 0).any() else 0,
                   avg_loss=round(r[r <= 0].mean() * 100, 1) if (r <= 0).any() else 0,
                   long_x=round(np.prod(1 + r[tr.lato == "long"]), 2), short_x=round(np.prod(1 + r[tr.lato == "short"]), 2),
                   senza_top1=round(CAP0 * np.prod(1 + r.drop(r.idxmax()))))
    return out


def bh(d, start=START, end=None):
    dd = d.loc[start:end or d.index[-1]]
    eq = CAP0 * (1 - COST) * dd.close / dd.open.iloc[0]
    e = pd.DataFrame(dict(eq=eq, inmkt=True))
    return metrics(e, pd.DataFrame())


def table(rows, cols):
    df = pd.DataFrame(rows)
    return df[[c for c in cols if c in df]].to_string(index=False)


COLS = ["asset", "regola", "finale", "rend_pct", "cagr_pct", "dd_pct", "mar", "trade", "wr_pct", "avg_win", "avg_loss",
        "long_x", "short_x", "tempo_mkt_pct", "senza_top1"]

if __name__ == "__main__":
    pd.set_option("display.width", 250)
    D = {a: load(s) for a, s in ASSETS.items()}
    W = {a: weekly(D[a]) for a in ASSETS}
    rows, rows_close = [], []
    for a in ASSETS:
        rows.append(dict(asset=a, regola="B&H", **bh(D[a])))
        for ru in RULES:
            eq, tr = run(D[a], W[a], ru)
            rows.append(dict(asset=a, regola=ru, **metrics(eq, tr)))
            eqc, trc = run(D[a], W[a], ru, fill="close")
            rows_close.append(dict(asset=a, regola=ru, **metrics(eqc, trc)))
            if ru in ("R1", "R4a", "R7"):
                tr.to_csv(os.path.join(HERE, f"trades_{a}_{ru}.csv"), index=False)
    res = pd.DataFrame(rows)
    res.to_csv(os.path.join(HERE, "results.csv"), index=False)
    print("== Dal 2021-01-01, fill open lunedì successivo, costi 0,1%/lato ==")
    print(table(rows, COLS))
    print("\n== Fill alla close del segnale (confronto) ==")
    print(table(rows_close, ["asset", "regola", "finale", "dd_pct", "mar", "trade"]))

    print("\n== Split 2021-2023 vs 2024-oggi (riparte flat da 10k) ==")
    sp = []
    for a in ASSETS:
        for ru in ["R1", "R4a", "R4b", "R5", "R7", "B&H"]:
            for lab, s, e in [("21-23", START, pd.Timestamp("2023-12-31")), ("24-oggi", pd.Timestamp("2024-01-01"), None)]:
                if ru == "B&H":
                    m = bh(D[a], s, e)
                else:
                    m = metrics(*run(D[a], W[a], ru, start=s, end=e))
                sp.append(dict(asset=a, regola=ru, periodo=lab, **m))
    print(table(sp, ["asset", "regola", "periodo", "finale", "cagr_pct", "dd_pct", "mar", "trade", "wr_pct"]))
    pd.DataFrame(sp).to_csv(os.path.join(HERE, "split.csv"), index=False)

    print("\n== Parametri MACD vicini ==")
    nb = []
    for fs in [(8, 21, 5), (12, 26, 9), (19, 39, 9)]:
        for a in ASSETS:
            w = weekly(D[a], *fs)
            for ru in ["R1", "R4a", "R7"]:
                nb.append(dict(param="/".join(map(str, fs)), asset=a, regola=ru, **metrics(*run(D[a], w, ru))))
    print(table(nb, ["param", "asset", "regola", "finale", "dd_pct", "mar", "trade", "wr_pct", "senza_top1"]))
    pd.DataFrame(nb).to_csv(os.path.join(HERE, "vicini.csv"), index=False)

    print("\n== Cross settimanali SOL dal 2021 ==")
    w = W["SOL"]
    x = w[(w.up | w.dn) & (w.close_date >= START)]
    print(pd.DataFrame(dict(chiusura=x.close_date.dt.date, cross=np.where(x.up, "UP", "DN"), close=x.close.round(1),
                            macd=x.macd.round(1), sopra_ema50=x.close > x.e50, low_sett=x.low.round(1),
                            high_sett=x.high.round(1))).to_string(index=False))
