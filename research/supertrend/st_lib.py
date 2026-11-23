"""supertrend · replica di ta.supertrend (TradingView, Pine v6), dati e stati. Nessun rendimento qui. Vedi PREREG.md / README.md.

Formula (manuale Pine, ta.supertrend(factor, atrPeriod)):
    TR_t   = max(high − low, |high − close_{t−1}|, |low − close_{t−1}|)      (prima barra: high − low)
    ATR_t  = RMA(TR, n): alla barra n−1 media semplice delle prime n TR, poi ATR_t = (ATR_{t−1}·(n−1) + TR_t) / n
    hl2    = (high + low) / 2
    su_t   = hl2 + factor·ATR_t          giù_t = hl2 − factor·ATR_t          (bande di base)
    banda inferiore finale: LB_t = giù_t se giù_t > LB_{t−1} oppure close_{t−1} < LB_{t−1}, altrimenti LB_{t−1}
    banda superiore finale: UB_t = su_t  se su_t  < UB_{t−1} oppure close_{t−1} > UB_{t−1}, altrimenti UB_{t−1}
    direzione: prima barra con ATR = +1 (ribasso); se la linea precedente era la banda superiore: −1 se close_t > UB_t,
               altrimenti +1; se era la banda inferiore: +1 se close_t < LB_t, altrimenti −1
    linea Supertrend = LB_t se direzione = −1 (rialzo, linea sotto il prezzo), UB_t se direzione = +1 (ribasso)
"""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CUT = "2026-11-15"            # fine dei test di strategia (dati congelati di W3.2)
END_DESC = "2026-11-22"       # fine del descrittivo e stato attuale
PERIODS = {"2018-20": ("2018-01-01", "2020-12-31"), "2021-23": ("2021-01-01", "2023-12-31"), "2024-26": ("2024-01-01", CUT)}
ATRS, FACTORS = (7, 10, 14, 21), (2.0, 2.5, 3.0, 4.0)


def rma_atr(h: np.ndarray, l: np.ndarray, c: np.ndarray, n: int) -> np.ndarray:
    """ta.atr(n) di TradingView: RMA della true range, seme = media semplice delle prime n TR; NaN prima."""
    N = len(c)
    tr = np.empty(N); tr[0] = h[0] - l[0]
    pc = c[:-1]
    tr[1:] = np.maximum(h[1:] - l[1:], np.maximum(np.abs(h[1:] - pc), np.abs(l[1:] - pc)))
    a = np.full(N, np.nan)
    if N < n:
        return a
    a[n - 1] = tr[:n].mean()
    for t in range(n, N):
        a[t] = (a[t - 1] * (n - 1) + tr[t]) / n
    return a


def supertrend(h, l, c, n: int = 10, factor: float = 3.0):
    """Ritorna (linea, direzione, banda inferiore finale, banda superiore finale, ATR). direzione −1 = rialzo, +1 = ribasso."""
    h, l, c = (np.asarray(x, float) for x in (h, l, c))
    N = len(c)
    atr = rma_atr(h, l, c, n)
    hl2 = (h + l) / 2
    ub0, lb0 = hl2 + factor * atr, hl2 - factor * atr
    ub, lb = np.full(N, np.nan), np.full(N, np.nan)
    d = np.ones(N, int); st = np.full(N, np.nan)
    for t in range(n - 1, N):
        plb = lb[t - 1] if t > 0 and not np.isnan(lb[t - 1]) else 0.0          # nz()
        pub = ub[t - 1] if t > 0 and not np.isnan(ub[t - 1]) else 0.0
        pc = c[t - 1] if t > 0 else np.nan
        lb[t] = lb0[t] if (lb0[t] > plb or pc < plb) else plb
        ub[t] = ub0[t] if (ub0[t] < pub or pc > pub) else pub
        if t == n - 1:                       # na(atr[1])
            d[t] = 1
        elif st[t - 1] == pub:               # la linea precedente era la banda superiore (ribasso)
            d[t] = -1 if c[t] > ub[t] else 1
        else:
            d[t] = 1 if c[t] < lb[t] else -1
        st[t] = lb[t] if d[t] == -1 else ub[t]
    return st, d, lb, ub, atr


def supertrend_alt(h, l, c, n: int = 10, factor: float = 3.0):
    """Seconda implementazione, scritta in modo diverso (liste, stato esplicito), per il controllo incrociato."""
    N = len(c); tr = [h[0] - l[0]] + [max(h[t] - l[t], abs(h[t] - c[t - 1]), abs(l[t] - c[t - 1])) for t in range(1, N)]
    atr = [None] * N; line = [None] * N; dr = [1] * N
    flb = fub = None; up = False
    for t in range(N):
        if t < n - 1:
            continue
        atr[t] = sum(tr[:n]) / n if t == n - 1 else atr[t - 1] + (tr[t] - atr[t - 1]) / n
        mid = (h[t] + l[t]) / 2
        nub, nlb = mid + factor * atr[t], mid - factor * atr[t]
        if t == n - 1:
            flb, fub, up = nlb, nub, False
        else:
            flb_new = nlb if (nlb > flb or c[t - 1] < flb) else flb
            fub_new = nub if (nub < fub or c[t - 1] > fub) else fub
            if up:
                up = not (c[t] < flb_new)
            else:
                up = c[t] > fub_new
            flb, fub = flb_new, fub_new
        dr[t] = -1 if up else 1
        line[t] = flb if up else fub
    return np.array([np.nan if x is None else x for x in line], float), np.array(dr)


# ---------- dati ----------
def load_4h(cut: str | None = None) -> pd.DataFrame:
    a = pd.read_csv(ROOT / "research" / "ema_sma" / "data" / "BTCUSDT_4h.csv.gz", index_col=0, parse_dates=True)
    return a[a.index < pd.Timestamp(cut) + pd.Timedelta(days=1)] if cut else a


def daily_from(a: pd.DataFrame, long_hist: bool = True) -> pd.DataFrame:
    """Giornaliero UTC dal 4h; prima del 17/08/2017 la storia del repo (f_long, dal 2014) per scaldare l'ATR."""
    d = a.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    if long_hist:
        f = pd.read_csv(ROOT / "research" / "p2_nuovi" / "data" / "f_long.csv.gz", index_col=0, parse_dates=True)
        d = pd.concat([f.loc[f.index < d.index[0], ["open", "high", "low", "close"]], d])
    return d


def weekly_from(d: pd.DataFrame) -> pd.DataFrame:
    """Settimanale W-SUN (lunedì–domenica UTC, come TradingView su BTCUSDT), solo settimane chiuse."""
    w = d.resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return w[w.index <= d.index[-1]]


def st_frame(b: pd.DataFrame, n: int = 10, factor: float = 3.0) -> pd.DataFrame:
    st, d, lb, ub, atr = supertrend(b["high"].to_numpy(), b["low"].to_numpy(), b["close"].to_numpy(), n, factor)
    return pd.DataFrame(dict(open=b["open"], high=b["high"], low=b["low"], close=b["close"], atr=atr, lb=lb, ub=ub, st=st, dir=d), index=b.index)


def to_base(s: pd.Series, idx: pd.DatetimeIndex, tf: str, base: str = "4h") -> np.ndarray:
    """Porta una serie 1D/1W sulla griglia di base: il valore della barra chiusa è noto dalla chiusura dell'ultima barra
    di base del giorno / della domenica (4h: candela delle 20:00) in poi."""
    off = pd.Timedelta(hours=20) if (base == "4h" and tf in ("1D", "1W")) else pd.Timedelta(0)
    return pd.Series(s.to_numpy(), s.index + off).reindex(idx, method="ffill").to_numpy()


def atr_w14(w: pd.DataFrame) -> pd.Series:
    """ATR settimanale di W3.2 (ewm alpha 1/14), per il tetto di rischio."""
    c = w["close"]
    tr = pd.concat([w["high"] - w["low"], (w["high"] - c.shift()).abs(), (w["low"] - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / 14, adjust=False).mean()


# ---------- controlli della replica (nessun rendimento) ----------
EXC: dict = {}
CONV: dict = {}


def checks() -> None:
    a = load_4h(END_DESC); d = daily_from(a); w = weekly_from(d)
    for name, b in (("4h", a), ("1D", d), ("1W", w)):
        for n in ATRS:
            for k in FACTORS:
                h, l, c = (b[x].to_numpy(float) for x in ("high", "low", "close"))
                st, dr, lb, ub, atr = supertrend(h, l, c, n, k)
                st2, dr2 = supertrend_alt(list(h), list(l), list(c), n, k)
                v = slice(n - 1, None)
                assert np.array_equal(dr[v], dr2[v]) and np.allclose(st[v], st2[v], rtol=1e-12), (name, n, k)
                t = np.arange(n, len(c))
                upc = (dr[t] == -1) & (dr[t - 1] == -1); dnc = (dr[t] == 1) & (dr[t - 1] == 1)
                fu = (dr[t] == -1) & (dr[t - 1] == 1); fd = (dr[t] == 1) & (dr[t - 1] == -1)
                # Proprietà: in rialzo la linea non scende e la chiusura le sta sopra; in ribasso lo specchio.
                # Unica eccezione ammessa (comportamento reale del codice Pine, non un errore della replica): la barra di un
                # cambio in cui la banda "vecchia" dell'altro lato è rimasta dalla parte sbagliata del prezzo (candela con
                # ombra enorme: l'ATR fa saltare la banda oltre la chiusura). La banda viene riallineata alla barra dopo.
                e1 = upc & (st[t] < st[t - 1]); e2 = dnc & (st[t] > st[t - 1])
                e3 = (dr[t] == -1) & (c[t] < st[t]); e4 = (dr[t] == 1) & (c[t] > st[t])
                prevflip = np.r_[False, (fu | fd)[:-1]]
                assert not (e1 & ~prevflip).any() and not (e2 & ~prevflip).any(), "la linea arretra fuori dal caso ammesso"
                assert not (e3 & ~fu).any() and not (e4 & ~fd).any(), "chiusura dal lato sbagliato fuori dalla barra di cambio"
                EXC[(name, n, k)] = (int((fu | fd).sum()), int((e3 | e4).sum()), int((e1 | e2).sum()))
                assert (c[t][fu] > ub[t][fu]).all() and (c[t][fd] < lb[t][fd]).all(), "il cambio avviene sulla chiusura oltre la banda"
                # ATR: ricorsione di Wilder e seme SMA
                tr = np.r_[h[0] - l[0], np.maximum(h[1:] - l[1:], np.maximum(abs(h[1:] - c[:-1]), abs(l[1:] - c[:-1])))]
                assert abs(atr[n - 1] - tr[:n].mean()) < 1e-9 and np.isnan(atr[: n - 1]).all()
                assert np.allclose(atr[n:], (atr[n - 1:-1] * (n - 1) + tr[n:]) / n)
                # dipendenza dal punto di partenza della storia: stessa serie senza le prime 300 barre (1W: 100)
                cutn = 100 if name == "1W" else 300
                st3, dr3, *_ = supertrend(h[cutn:], l[cutn:], c[cutn:], n, k)
                same = (dr[cutn:] == dr3) & np.isclose(st[cutn:], st3, rtol=1e-6, equal_nan=False)
                CONV[(name, n, k)] = int(len(same) - np.argmax(~same[::-1])) if not same.all() else 0   # barre prima della coincidenza stabile
                assert same[-50:].all(), "non converge"
        f = st_frame(b)
        e = EXC[(name, 10, 3.0)]; tot = [sum(v[i] for kk, v in EXC.items() if kk[0] == name) for i in range(3)]
        print(f"{name} eccezioni 'banda vecchia' 10/3: {e[1]} barre di cambio su {e[0]}; su 16 combinazioni: {tot[1]} su {tot[0]} cambi")
        print(f"{name} barre perché due storie con inizio diverso coincidano (10/3; massimo sulle 16): {CONV[(name, 10, 3.0)]}; {max(v for kk, v in CONV.items() if kk[0] == name)}")
        print(f"{name}: {len(b)} barre, {b.index[0]} → {b.index[-1]} | 10/3: cambi totali {(np.diff(f['dir'].to_numpy()[10:]) != 0).sum()} | controlli superati (16 combinazioni)")


def hand_table(tf: str = "1D", around: str = "2026-11-01", rows: int = 16) -> pd.DataFrame:
    """Tabella per la verifica a mano: 16 barre con TR, ATR, bande di base e finali, direzione, linea."""
    a = load_4h(END_DESC); b = {"4h": a, "1D": daily_from(a), "1W": weekly_from(daily_from(a))}[tf]
    f = st_frame(b); c = f["close"]
    f["tr"] = np.maximum(f["high"] - f["low"], np.maximum((f["high"] - c.shift()).abs(), (f["low"] - c.shift()).abs()))
    f["hl2"] = (f["high"] + f["low"]) / 2
    f["su"] = f["hl2"] + 3 * f["atr"]; f["giu"] = f["hl2"] - 3 * f["atr"]
    i = f.index.searchsorted(pd.Timestamp(around))
    return f.iloc[i - rows // 2: i + rows // 2][["high", "low", "close", "tr", "atr", "hl2", "su", "giu", "ub", "lb", "dir", "st"]]


if __name__ == "__main__":
    checks()
