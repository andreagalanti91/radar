"""supertrend · motore barra per barra (griglia di base 4h per BTC, 1D per ETH). Vedi PREREG.md §4."""
from __future__ import annotations
import numpy as np, pandas as pd
import st_lib as L

FEE_SPOT, FEE_PERP, SLIP = 0.001, 0.0005, 0.001
START = "2018-01-01"
STRATS = ["S1_4h", "S2_4h", "S3_4h", "S1_1D", "S2_1D", "S3_1D", "S1_1W", "S2_1W", "S3_1W", "S4a", "S4b"]
EXTRA = ["S4a_long", "S4a_short", "S4b_long", "S4b_short"]


def funding_btc() -> pd.Series:
    f = pd.read_csv(L.ROOT / "research" / "p2_nuovi" / "data" / "f_long.csv.gz", index_col=0, parse_dates=True)
    return f["funding"].fillna(0.0)


def base_btc(a: pd.DataFrame | None = None, long_hist: bool = True) -> dict:
    """Griglia 4h di BTC con giornaliero e settimanale derivati."""
    a = L.load_4h(L.CUT) if a is None else a
    d = L.daily_from(a, long_hist); w = L.weekly_from(d); idx = a.index
    fu = pd.Series(L.to_base(funding_btc(), idx, "4h"), idx).ffill().fillna(0.0).to_numpy() / 6.0
    dn = idx.normalize()
    return dict(base="4h", idx=idx, O=a["open"].to_numpy(float), H=a["high"].to_numpy(float), Lo=a["low"].to_numpy(float),
                C=a["close"].to_numpy(float), fu=fu, last=np.r_[dn[1:] != dn[:-1], True], bars={"4h": a, "1D": d, "1W": w},
                atrw=L.to_base(L.atr_w14(w), idx, "1W", "4h"))


def base_daily(d: pd.DataFrame, funding: pd.Series) -> dict:
    """Griglia giornaliera (ETH): niente 4h."""
    w = L.weekly_from(d); idx = d.index
    return dict(base="1D", idx=idx, O=d["open"].to_numpy(float), H=d["high"].to_numpy(float), Lo=d["low"].to_numpy(float),
                C=d["close"].to_numpy(float), fu=funding.reindex(idx).fillna(0.0).to_numpy(), last=np.ones(len(idx), bool),
                bars={"1D": d, "1W": w}, atrw=L.to_base(L.atr_w14(w), idx, "1W", "1D"))


def directions(B: dict, n: int = 10, k: float = 3.0) -> dict:
    """Direzione del Supertrend di ogni intervallo sulla griglia di base (nota alla chiusura della barra di base)."""
    out = {}
    for tf, b in B["bars"].items():
        d = pd.Series(L.supertrend(b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy(), n, k)[1], b.index)
        out[tf] = d.to_numpy() if tf == B["base"] else np.nan_to_num(L.to_base(d, B["idx"], tf, B["base"]), nan=1).astype(int)
    return out


def targets(D: dict) -> dict:
    """Posizione desiderata (+1 long, −1 short, 0 fuori) per ogni strategia. direzione −1 = rialzo."""
    T = {}
    for tf, d in D.items():
        up = d == -1
        T[f"S1_{tf}"] = np.where(up, 1, -1); T[f"S2_{tf}"] = np.where(up, 1, 0); T[f"S3_{tf}"] = np.where(up, 0, -1)
    for name, hi, lo in (("S4a", "1W", "1D"), ("S4b", "1D", "4h")):
        if hi in D and lo in D:
            t = np.where((D[hi] == -1) & (D[lo] == -1), 1, np.where((D[hi] == 1) & (D[lo] == 1), -1, 0))
            T[name] = t; T[name + "_long"] = np.maximum(t, 0); T[name + "_short"] = np.minimum(t, 0)
    return T


def run(B: dict, tgt: np.ndarray, i0: int, i1: int, cap: bool = False):
    """Simula le barre [i0, i1). Ritorna (equity a fine giornata, date, trade [ingresso, uscita, lato, pnl])."""
    O, H, Lo, C, fu, last, atrw = B["O"], B["H"], B["Lo"], B["C"], B["fu"], B["last"], B["atrw"]
    pos, cash, qty, pxe, eq, eq0, ib, stop, blocked = 0, 1.0, 0.0, 0.0, 1.0, 1.0, 0, np.nan, None
    E, days, T = [], [], []
    tg = tgt.tolist()
    for i in range(i0, i1):
        want = tg[i - 1]
        if blocked is not None:
            if want != blocked:
                blocked = None
            else:
                want = 0
        o = O[i]
        if want != pos:
            if pos > 0:
                eq = cash + qty * o * (1 - SLIP) * (1 - FEE_SPOT)
            elif pos < 0:
                px = o * (1 + SLIP); eq = cash + qty * (pxe - px) - qty * px * FEE_PERP
            if pos:
                T.append((ib, i, pos, eq / eq0 - 1)); cash = eq; qty = 0.0
            pos = want
            if pos:
                x = min(1.0, 0.25 / (2.5 * atrw[i - 1] / C[i - 1])) if cap else 1.0
                eq0, ib = eq, i
                if pos > 0:
                    px = o * (1 + SLIP); qty = x * eq * (1 - FEE_SPOT) / px; cash = eq * (1 - x)
                else:
                    px = o * (1 - SLIP); qty = x * eq / px; cash = eq - qty * px * FEE_PERP
                pxe = px
                stop = C[i - 1] - pos * 2.5 * atrw[i - 1] if cap else np.nan
        if cap and pos:
            if pos > 0 and Lo[i] <= stop:
                eq = cash + qty * min(o, stop) * (1 - SLIP) * (1 - FEE_SPOT)
                T.append((ib, i, pos, eq / eq0 - 1)); cash, qty, pos, blocked = eq, 0.0, 0, tg[i - 1]
            elif pos < 0 and H[i] >= stop:
                px = max(o, stop) * (1 + SLIP); eq = cash + qty * (pxe - px) - qty * px * FEE_PERP
                T.append((ib, i, pos, eq / eq0 - 1)); cash, qty, pos, blocked = eq, 0.0, 0, tg[i - 1]
        if pos > 0:
            eq = cash + qty * C[i]
        elif pos < 0:
            cash += qty * C[i] * fu[i]; eq = cash + qty * (pxe - C[i])
        if last[i]:
            E.append(eq); days.append(i)
    if pos:
        T.append((ib, i1 - 1, pos, eq / eq0 - 1))
    return np.array(E), B["idx"][days].normalize(), np.array(T, float).reshape(-1, 4)


def metrics(E: np.ndarray, days: pd.DatetimeIndex, T: np.ndarray, idx: pd.DatetimeIndex, a: str, b: str) -> dict:
    """Metriche del periodo [a, b] come fetta della curva continua."""
    m = (days >= a) & (days <= b); j0 = np.flatnonzero(m)[0]
    base = E[j0 - 1] if j0 > 0 else 1.0
    e = np.r_[base, E[m]] / base
    yrs = ((pd.Timestamp(b) - pd.Timestamp(a)).days + 1) / 365.25
    fin = e[-1]; cagr = fin ** (1 / yrs) - 1 if fin > 0 else -1.0
    dd = float((e / np.maximum.accumulate(e) - 1).min())
    out = dict(fin=fin * 10000, cagr=cagr, dd=dd, S=cagr / abs(dd) if dd < 0 else (99.0 if cagr > 0 else 0.0), n=0, wr=np.nan, fin_no2=fin * 10000)
    if len(T):
        tb = idx[T[:, 0].astype(int)]
        p = T[(tb >= a) & (tb < pd.Timestamp(b) + pd.Timedelta(days=1)), 3]
        if len(p):
            out.update(n=len(p), wr=float((p > 0).mean()), fin_no2=fin * 10000 / float(np.prod(1 + np.sort(p)[::-1][:2])))
    return out


def bh(B: dict, a: str, b: str) -> dict:
    d = B["bars"]["1D"]; x = d[(d.index >= a) & (d.index <= b)]
    e = np.r_[1.0, x["close"].to_numpy() / (x["open"].iloc[0] * (1 + SLIP)) * (1 - FEE_SPOT)]
    yrs = ((pd.Timestamp(b) - pd.Timestamp(a)).days + 1) / 365.25
    cagr = e[-1] ** (1 / yrs) - 1; dd = float((e / np.maximum.accumulate(e) - 1).min())
    return dict(fin=e[-1] * 10000, cagr=cagr, dd=dd, S=cagr / abs(dd), n=1, wr=np.nan, fin_no2=np.nan)


def span(B: dict, a: str = START, b: str = L.CUT) -> tuple[int, int]:
    return int(B["idx"].searchsorted(pd.Timestamp(a))), int(B["idx"].searchsorted(pd.Timestamp(b) + pd.Timedelta(days=1)))


def permute(a: pd.DataFrame, p0: str, p1: str, rng: np.random.Generator, block: int = 120) -> pd.DataFrame:
    """Serie con [p0, p1] rimescolato a blocchi (rapporti O/H/L/C sulla chiusura precedente); il resto reale."""
    i0 = a.index.searchsorted(pd.Timestamp(p0)); i1 = a.index.searchsorted(pd.Timestamp(p1) + pd.Timedelta(days=1))
    v = a[["open", "high", "low", "close"]].to_numpy()
    r = v[i0:i1] / v[i0 - 1:i1 - 1, 3:4]
    nb = int(np.ceil(len(r) / block)); order = rng.permutation(nb)
    r = np.vstack([r[j * block:(j + 1) * block] for j in order])
    c = v[i0 - 1, 3] * np.cumprod(r[:, 3]); prev = np.r_[v[i0 - 1, 3], c[:-1]]
    out = a.iloc[:i1].copy()
    out.iloc[i0:i1, [out.columns.get_loc(x) for x in ("open", "high", "low", "close")]] = r * prev[:, None]
    return out


PER = dict(L.PERIODS); PER_ALL = {**PER, "2021-26": ("2021-01-01", L.CUT), "2018-26": (START, L.CUT)}


def evaluate(B: dict, tgt: np.ndarray, cap: bool = False, periods: dict = PER_ALL) -> dict:
    i0, i1 = span(B)
    E, days, T = run(B, tgt, i0, i1, cap)
    return {p: metrics(E, days, T, B["idx"], a, b) for p, (a, b) in periods.items()}
