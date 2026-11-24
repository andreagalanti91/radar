"""zeiierman3 · dati, indicatore (porting importato da research/zeiierman/ztp.py), motore stand-alone. Vedi PREREG.md."""
from __future__ import annotations
import sys
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "zeiierman"))
sys.path.insert(0, str(ROOT / "research" / "ema_sma"))
from ztp import ztp, atr  # noqa: E402  porting verificato, non riscritto
import es_lib  # noqa: E402

FEE, SLIP, CAP = 0.001, 0.001, 10_000.0
END = "2026-11-22"
PERIODS = {"P1 2018-20": ("2018-01-01", "2020-12-31"), "P2 2021-23": ("2021-01-01", "2023-12-31"),
           "P3 2024-26": ("2024-01-01", END), "dal 2021": ("2021-01-01", END)}


def load():
    a = es_lib.load_4h(cut=None)
    a = a[a.index <= pd.Timestamp(END) + pd.Timedelta(hours=20)][["open", "high", "low", "close"]].astype(float)
    d = es_lib.daily_from(a)[["open", "high", "low", "close"]].astype(float)
    d = d[d.index <= END]
    return d, a


def funding():
    f = pd.read_csv(ROOT / "research" / "p2_nuovi" / "data" / "f_long.csv.gz", index_col=0, parse_dates=True)["funding"]
    r = pd.read_csv(ROOT / "data" / "funding.csv", parse_dates=["date"]).set_index("date")["funding"]
    s = pd.concat([f, r[r.index > f.index[-1]]]).fillna(0.0)
    return s[~s.index.duplicated()]


def indicators(df):
    z = ztp(df)
    z["atr"] = atr(df, 14)
    return z


def cross_below(x, th):
    p = np.r_[np.nan, x[:-1]]
    return (x < th) & (p >= th)


def cross_above(x, th):
    p = np.r_[np.nan, x[:-1]]
    return (x > th) & (p <= th)


def rule_signals(z, rule, line="tz", ent=-90.0, ex=-20.0):
    """(entry, exit) booleani alla chiusura. R1/R3: scende sotto ent; R2: risale sopra ent; uscita x > ex (stato).
    R4 short: sale sopra ex, copertura x < ent. R5: rilascio blu (−70) / rilascio rosso (−30) su tz (ent/ex = soglie)."""
    x = z[line].to_numpy(float)
    if rule in ("R1", "R3"):
        return cross_below(x, ent), x > ex
    if rule == "R2":
        return cross_above(x, ent), x > ex
    if rule == "R4":
        return cross_above(x, ex), x < ent
    if rule == "R5":
        return cross_above(x, ent), cross_below(x, ex)
    raise ValueError(rule)


def simulate(df, z, rule, start, end, line="tz", ent=-90.0, ex=-20.0, stop=None, side=1, gate=None, force_exit=None,
             fund=None, bars_per_day=1, entries=None):
    """Una posizione per volta, 1x. stop: None | ('atr', k) | ('low', n). gate: array bool (True = ingresso permesso).
    force_exit: array bool (True alla barra = esci all'apertura di quella barra). entries: lista (i_in, i_out) per il placebo."""
    idx = df.index
    O, H, L, C = (df[k].to_numpy(float) for k in ("open", "high", "low", "close"))
    A = z["atr"].to_numpy(float)
    en, xx = rule_signals(z, rule, line, ent, ex) if entries is None else (None, None)
    fu = (fund.reindex(idx.normalize()).fillna(0.0).to_numpy() / bars_per_day) if (fund is not None and side < 0) else np.zeros(len(idx))
    i0 = idx.searchsorted(pd.Timestamp(start))
    i1 = idx.searchsorted(pd.Timestamp(end) + pd.Timedelta(days=1)) - 1
    cash, qty, pend_in, pend_out, trades = 1.0, 0.0, False, None, []
    eq = np.full(i1 - i0 + 1, np.nan)
    pos = 0
    plan = dict(entries) if entries is not None else None
    exit_at = None

    def close(px_raw, i, why):
        nonlocal cash, qty, pos
        px = px_raw * (1 - SLIP * pos)
        cash += qty * px - abs(qty) * px * FEE
        trades.append(dict(ingresso=idx[ie], uscita=idx[i], px_in=pin, px_out=px, motivo=why, pnl=cash / c0 - 1,
                           barre=i - ie))
        qty, pos = 0.0, 0

    for i in range(i0, i1 + 1):
        if pos and force_exit is not None and force_exit[i]:
            close(O[i], i, "W3.2")
        if pos and pend_out:
            close(O[i], i, pend_out)
        if not pos and pend_in:
            pos = side; pin = O[i] * (1 + SLIP * side); c0 = cash
            qty = side * cash / pin
            cash -= qty * pin + abs(qty) * pin * FEE
            ie = i
            sp = None
            if stop is not None:
                if stop[0] == "atr":
                    sp = pin - side * stop[1] * A[i - 1]
                else:
                    sp = L[max(0, i - stop[1]):i].min() if side > 0 else H[max(0, i - stop[1]):i].max()
            if plan is not None:
                exit_at = plan[i]
        pend_in, pend_out = False, None
        if pos and sp is not None and ((side > 0 and L[i] <= sp) or (side < 0 and H[i] >= sp)):
            close(min(O[i], sp) if side > 0 else max(O[i], sp), i, "stop")
        if pos:
            cash -= qty * C[i] * fu[i]
        eq[i - i0] = cash + qty * C[i] - abs(qty) * C[i] * (FEE + SLIP) if pos else cash
        if i == i1:
            break
        if plan is not None:
            if pos and i + 1 >= exit_at:
                pend_out = "placebo"
            elif not pos and (i + 1) in plan:
                pend_in = True
            continue
        if pos:
            if xx[i]:
                pend_out = "segnale"
        elif en[i] and (gate is None or gate[i]):
            pend_in = True
    if pos:
        close(C[i1], i1, "fine")
        eq[-1] = cash
    t = pd.DataFrame(trades)
    curve = pd.Series(eq * CAP, idx[i0:i1 + 1])
    return t, curve


def daily_curve(curve):
    return curve.groupby(curve.index.normalize()).last()


def metrics(t, curve):
    c = daily_curve(curve)
    fin = float(c.iloc[-1]); yrs = (c.index[-1] - c.index[0]).days / 365.25 + 1 / 365.25
    dd = float((c / c.cummax() - 1).min())
    cagr = (fin / CAP) ** (1 / yrs) - 1 if fin > 0 else -1.0
    n = len(t)
    return dict(finale=round(fin), rend=round((fin / CAP - 1) * 100, 1), cagr=round(cagr * 100, 1), dd=round(dd * 100, 1),
                cagr_dd=round(cagr / abs(dd), 2) if dd < 0 else np.nan,
                mar=round((fin / CAP - 1) / abs(dd), 2) if dd < 0 else np.nan, trade=n,
                wr=round(float((t.pnl > 0).mean() * 100)) if n else np.nan,
                espo=round(float(t.barre.sum()) / max(len(curve), 1) * 100) if n else 0)


def buyhold(df, start, end):
    s = df.loc[start:end]
    c = s.close / (s.open.iloc[0] * (1 + SLIP)) * (1 - FEE) * CAP
    t = pd.DataFrame(dict(pnl=[c.iloc[-1] / CAP - 1], barre=[len(s)]))
    return metrics(t, c)


def without_top(t, k=2):
    if len(t) == 0:
        return CAP
    g = t.pnl.sort_values(ascending=False).iloc[k:]
    return round(CAP * float(np.prod(1 + g)))
