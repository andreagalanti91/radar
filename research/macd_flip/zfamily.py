"""Famiglia Z: "pallino verde sotto lo zero" (cross_UP con macd<0) sul MACD 1W 12/26/9, + EMA/SMA.

Uso: python research/macd_flip/zfamily.py   (richiede data/ da fetch.py; riusa barre/metriche di backtest.py)
Stesse ipotesi di backtest.py: fill open lunedì successivo, 0,1%/lato, funding 0, 1x, 10k al 2021-01-01, DD 1d.

Regole preregistrate (identiche su BTC/ETH/SOL):
 Z1  long su cross_UP con macd<0; uscita al primo cross_DN (qualsiasi)
 Z2  Z1 + short speculare: short su cross_DN con macd>0, uscita al primo cross_UP (flip ammesso)
 Z3  Z1 ma ingresso solo quando close>EMA20, entro 4 settimane dal pallino (sett. 0..4), altrimenti salta;
     armamento annullato da un cross_DN; uscita su cross_DN
 Z4  ingresso Z1; uscita "trend": close<EMA50 oppure cross_DN con macd>0. Poiché il pallino sotto zero cade
     quasi sempre con prezzo <EMA50, l'uscita EMA50 si arma solo dopo la prima close>EMA50; prima di allora
     si esce sul cross_DN qualsiasi (come Z1)
 Z5a Z1 solo se close > SMA200 1W al pallino;  Z5b Z1 solo se close < SMA200.
     SMA200 mancante (SOL prima di ~giu 2024) -> ripiego EMA200 (calcolata dal 2020-08: poco affidabile)
 Z6  Z4 + short speculare: short su cross_DN con macd>0; uscita close>EMA50 (armata dopo la prima close<EMA50)
     oppure cross_UP con macd<0; prima dell'armamento uscita su cross_UP qualsiasi
"""
import os
import numpy as np, pandas as pd
import backtest as B

HERE = B.HERE
ZR = ["Z1", "Z2", "Z3", "Z4", "Z5a", "Z5b", "Z6"]


def regime_ref(r):
    return r.sma200 if not np.isnan(r.sma200) else r.e200


def orders_for(rule, w, start, end):
    """macchina a stati settimanale -> {giorno esecuzione: posizione target}"""
    ww = w[(w.close_date >= start) & (w.close_date <= end)]
    pos, armed, wait, orders = 0, False, None, {}
    for t, r in ww.iterrows():
        green = r.up and r.macd < 0
        red = r.dn and r.macd > 0
        tg = pos
        if pos == 1:
            if rule in ("Z4", "Z6"):
                if r.close > r.e50:
                    armed = True
                if (armed and r.close < r.e50) or red or (not armed and r.dn):
                    tg = 0
            elif r.dn:
                tg = 0
        elif pos == -1:
            if rule == "Z2":
                if r.up:
                    tg = 0
            else:  # Z6
                if r.close < r.e50:
                    armed = True
                if (armed and r.close > r.e50) or green or (not armed and r.up):
                    tg = 0
        if tg == 0:
            entry_long = False
            if rule in ("Z1", "Z2", "Z4", "Z6") and green:
                entry_long = True
            elif rule == "Z5a" and green and r.close > regime_ref(r):
                entry_long = True
            elif rule == "Z5b" and green and r.close < regime_ref(r):
                entry_long = True
            elif rule == "Z3":
                if green:
                    wait = 0
                elif wait is not None:
                    wait += 1
                if r.dn or (wait is not None and wait > 4):
                    wait = None
                if wait is not None and r.close > r.e20:
                    entry_long, wait = True, None
            if entry_long:
                tg = 1
            elif rule in ("Z2", "Z6") and red:
                tg = -1
            if tg != pos:
                armed = False
                if tg == 1 and r.close > r.e50:
                    armed = True
                if tg == -1 and r.close < r.e50:
                    armed = True
        if tg != pos:
            orders[r.close_date + pd.Timedelta(days=1)] = (tg, t)
            pos = tg
    return orders


def simulate(d, orders, start, end=None):
    end = end or d.index[-1]
    dd = d.loc[start:end]
    eq_base, pos, cur, trades, eqs = B.CAP0, 0, None, [], []

    def close_trade(day, px, why):
        nonlocal eq_base, pos, cur
        g = max(0.0, 1 + pos * (px / cur["px_in"] - 1))
        eq_base = eq_base * (1 - B.COST) ** 2 * g
        cur.update(uscita=day.date(), prezzo_uscita=round(px, 4), motivo=why,
                   pnl_pct=round(((1 - B.COST) ** 2 * g - 1) * 100, 2), capitale=round(eq_base))
        trades.append(cur); pos, cur = 0, None

    for day, b in dd.iterrows():
        o = orders.get(day)
        if o is not None:
            tg, sw = o
            if pos != 0 and tg != pos:
                close_trade(day, b.open, "segnale")
            if tg != 0 and pos == 0:
                pos = tg
                cur = dict(segnale=(sw + pd.Timedelta(days=6)).date(), ingresso=day.date(),
                           lato="long" if tg == 1 else "short", prezzo_ingresso=round(b.open, 4), px_in=b.open)
        if pos == -1 and b.high >= 2 * cur["px_in"]:
            close_trade(day, 2 * cur["px_in"], "liquidato")
        mtm = eq_base if pos == 0 else eq_base * (1 - B.COST) * (1 + pos * (b.close / cur["px_in"] - 1))
        eqs.append((day, mtm, pos != 0))
    if pos != 0:
        close_trade(dd.index[-1], dd.close.iloc[-1], "aperto")
    eq = pd.DataFrame(eqs, columns=["date", "eq", "inmkt"]).set_index("date")
    tr = pd.DataFrame(trades)
    return eq, (tr.drop(columns="px_in") if len(tr) else tr)


def runz(d, w, rule, start=B.START, end=None):
    end = end or d.index[-1]
    return simulate(d, orders_for(rule, w, start, end), start, end)


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    D = {a: B.load(s) for a, s in B.ASSETS.items()}
    W = {}
    for a in B.ASSETS:
        w = B.weekly(D[a]); w["e200"] = B.ema(w.close, 200); W[a] = w
    rows, TR = [], {}
    for a in B.ASSETS:
        rows.append(dict(asset=a, regola="B&H", **B.bh(D[a])))
        for ru in ZR:
            eq, tr = runz(D[a], W[a], ru)
            TR[a, ru] = tr
            rows.append(dict(asset=a, regola=ru, **B.metrics(eq, tr)))
            if ru in ("Z1", "Z4", "Z6"):
                tr.to_csv(os.path.join(HERE, f"trades_{a}_{ru}.csv"), index=False)
    pd.DataFrame(rows).to_csv(os.path.join(HERE, "results_z.csv"), index=False)
    print("== Famiglia Z dal 2021-01-01 ==")
    print(B.table(rows, B.COLS))

    print("\n== Pallini verdi sotto zero dal 2021 (esito Z1 / Z4) ==")
    for a in B.ASSETS:
        w = W[a]
        g = w[w.up & (w.macd < 0) & (w.close_date >= B.START)]
        for t, r in g.iterrows():
            sd = r.close_date.date()
            out = []
            for ru in ("Z1", "Z4"):
                x = TR[a, ru]; x = x[x.segnale == sd] if len(x) else x
                out.append(f"{ru}: {x.prezzo_uscita.iloc[0]:.2f} {x.uscita.iloc[0]} {x.motivo.iloc[0]} {x.pnl_pct.iloc[0]:+.1f}%"
                           if len(x) else f"{ru}: (già in posizione)")
            ref = regime_ref(r)
            print(f"{a} {sd} close {r.close:.2f} macd {r.macd:.2f} {'>' if r.close > ref else '<'}SMA200* "
                  f"{'>' if r.close > r.e200 else '<'}EMA200 {'>' if r.close > r.e50 else '<'}EMA50 | " + " | ".join(out))

    print("\n== Split 2021-23 / 2024-oggi ==")
    sp = []
    for a in B.ASSETS:
        for ru in ZR + ["B&H"]:
            for lab, s, e in [("21-23", B.START, pd.Timestamp("2023-12-31")), ("24-oggi", pd.Timestamp("2024-01-01"), None)]:
                m = B.bh(D[a], s, e) if ru == "B&H" else B.metrics(*runz(D[a], W[a], ru, s, e))
                sp.append(dict(asset=a, regola=ru, periodo=lab, **m))
    print(B.table(sp, ["asset", "regola", "periodo", "finale", "cagr_pct", "dd_pct", "mar", "trade", "wr_pct"]))
    pd.DataFrame(sp).to_csv(os.path.join(HERE, "split_z.csv"), index=False)

    print("\n== Parametri MACD vicini ==")
    nb = []
    for fs in [(8, 21, 5), (12, 26, 9), (19, 39, 9)]:
        for a in B.ASSETS:
            w = B.weekly(D[a], *fs); w["e200"] = B.ema(w.close, 200)
            for ru in ZR:
                nb.append(dict(param="/".join(map(str, fs)), asset=a, regola=ru, **B.metrics(*runz(D[a], w, ru))))
    print(B.table(nb, ["param", "asset", "regola", "finale", "dd_pct", "mar", "trade", "wr_pct", "senza_top1"]))
    pd.DataFrame(nb).to_csv(os.path.join(HERE, "vicini_z.csv"), index=False)
