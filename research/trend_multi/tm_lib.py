"""trend_multi · motore (PREREG.md, commit 3ca3620). Solo numpy/pandas."""
from pathlib import Path
import numpy as np
import pandas as pd

D = Path(__file__).resolve().parent / "data"
CLASSES = {"azioni": "SPY QQQ IWM EFA VGK EEM EWJ".split(), "obbligazioni": "IEF TLT LQD HYG".split(),
           "materie prime": "GLD SLV DBC USO".split(), "valute": "UUP FXE FXY".split(), "immobiliare": ["VNQ"]}
UNIVERSE = [t for v in CLASSES.values() for t in v]
SIM0, J0, J1, HALF = "2007-01-31", "2016-01-01", "2026-11-20", "2021-01-01"
MINHIST = 273


def _ser(path):
    d = pd.read_csv(path, index_col=0, parse_dates=True)
    return d["adj"] if "adj" in d else d["close"]


def load(extra=None):
    """Prezzi rettificati (calendario SPY), tasso giornaliero T-bill, SHY. extra: {nome: percorso} di altre serie."""
    ser = {t: _ser(D / f"{t}.csv.gz") for t in UNIVERSE + ["SHY"]}
    ser.update({k: _ser(v) for k, v in (extra or {}).items()})
    px = pd.DataFrame(ser)
    px = px.loc[px["SPY"].notna()].loc[:J1]
    first = {t: px[t].first_valid_index() for t in px}
    px = px.ffill()
    irx = pd.read_csv(D / "IRX.csv.gz", index_col=0, parse_dates=True)["close_raw"].reindex(px.index).ffill()
    rf = (irx / 100 / 252).shift(1).fillna(0.0)          # tasso noto alla chiusura precedente
    return px.drop(columns="SHY"), rf, px["SHY"].pct_change().fillna(0.0), first


def signals(px, cash_idx, kind, side):
    """kind: tuple di orizzonti in sedute, oppure ('sma', n). side: 'LF' | 'LS'. Segnale alla chiusura del giorno."""
    if kind[0] == "sma":
        up = (px > px.rolling(kind[1]).mean()).astype(float).where(px.rolling(kind[1]).mean().notna())
        s = up if side == "LF" else 2 * up - 1
    else:
        parts = []
        for h in kind:
            ex = px.pct_change(h, fill_method=None).sub(cash_idx.pct_change(h), axis=0)
            parts.append(((ex > 0).astype(float) if side == "LF" else np.sign(ex)).where(ex.notna()))
        s = sum(parts) / len(parts)
    return s


def rebal_days(idx, freq):
    """Giorni di decisione: ultima seduta del mese ('M') o della settimana ('W')."""
    key = idx.to_period("M") if freq == "M" else idx.to_period("W-SUN")
    s = pd.Series(idx, index=idx)
    return set(s.groupby(key).last().values)


def run(px, rf, cash_ret=None, kind=(21, 63, 252), side="LF", freq="M", L=1.0, vol_n=60, tgt=0.10, cost=0.001,
        borrow=0.01, band=0.0, drop=(), start=SIM0, fixed=None, fund_long=0.0, cls=None):
    """fund_long: costo annuo sul nozionale long (funding dei perpetui). cls: {mercato: classe} per rischio uguale per classe.
    Simula. fixed: funzione(giorno, disponibili) -> pesi target (per i riferimenti). Ritorna dict con equity e diagnostica."""
    cash_ret = rf if cash_ret is None else cash_ret
    cols = [c for c in px.columns if c not in drop]
    px = px[cols]
    ret = px.pct_change(fill_method=None)
    hist = px.notna().cumsum()
    cash_idx = (1 + rf).cumprod()                           # il segnale è sempre l'eccesso sul T-bill
    sig = signals(px, cash_idx, kind, side) if fixed is None else None
    idx = px.index
    dec = rebal_days(idx, freq)
    R = ret.to_numpy()
    n = len(cols)
    w = np.zeros(n); eq = 1.0; pend = None
    t0 = idx.searchsorted(pd.Timestamp(start))
    E = np.full(len(idx), np.nan); G = np.zeros(len(idx)); TO = np.zeros(len(idx)); NORD = np.zeros(len(idx))
    W = np.zeros((len(idx), n)); TGT = {}; SIG = {}
    for i in range(t0, len(idx)):
        r = np.nan_to_num(R[i])
        gross = np.abs(w).sum()
        pnl = (w * r).sum() + (1 - gross) * cash_ret.iat[i] - borrow / 252 * np.abs(w[w < 0]).sum() - fund_long / 252 * w[w > 0].sum()
        w = w * (1 + r) / (1 + pnl); eq *= 1 + pnl               # deriva delle posizioni
        if pend is not None:                                      # esecuzione alla chiusura della seduta successiva alla decisione
            d = pend - w
            if band > 0:
                d = np.where(np.abs(d) >= band, d, 0.0)
            tr = np.abs(d).sum()
            eq *= 1 - tr * cost; w = (w + d) / (1 - tr * cost)
            TO[i] = tr; NORD[i] = (np.abs(d) >= 0.01).sum(); pend = None
        E[i] = eq; G[i] = np.abs(w).sum(); W[i] = w
        if idx[i] in dec:
            ok = (hist.iloc[i].to_numpy() >= MINHIST)
            if fixed is not None:
                pend = fixed(idx[i], cols, ok)
            else:
                s = np.nan_to_num(sig.iloc[i].to_numpy()) * ok
                win = ret.iloc[i - vol_n + 1:i + 1]
                sd = np.maximum(win.std().to_numpy() * np.sqrt(252), 0.01)
                u = np.where(ok & np.isfinite(sd), s / sd, 0.0)
                if cls is not None:
                    cl = np.array([cls[c] for c in cols])
                    for k in set(cl):
                        u[cl == k] /= max((ok & (cl == k)).sum(), 1)
                cov = win.fillna(0).cov().to_numpy() * 252
                pv = float(np.sqrt(max(u @ cov @ u, 0)))
                tw = u * (tgt / pv) if pv > 0 else u * 0
                g = np.abs(tw).sum()
                if g > L:
                    tw *= L / g
                pend = tw; SIG[idx[i]] = s
            TGT[idx[i]] = pend.copy()
    e = pd.Series(E, idx).dropna()
    return dict(eq=e, gross=pd.Series(G, idx).loc[e.index], to=pd.Series(TO, idx).loc[e.index],
                nord=pd.Series(NORD, idx).loc[e.index], w=pd.DataFrame(W, idx, cols).loc[e.index],
                tgt=pd.DataFrame(TGT, index=cols).T, sig=pd.DataFrame(SIG, index=cols).T)


def fixed_6040(day, cols, ok):
    return np.array([0.6 if c == "SPY" else 0.4 if c == "IEF" else 0.0 for c in cols])


def fixed_ew(day, cols, ok):
    return ok / max(ok.sum(), 1)


def fixed_cash(day, cols, ok):
    return np.zeros(len(cols))


def metrics(e, rf, a, b):
    e = e.loc[a:b]; e = e / e.iloc[0]
    r = e.pct_change().dropna()
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    cagr = e.iloc[-1] ** (1 / yrs) - 1
    dd = (e / e.cummax() - 1).min()
    x = r - rf.reindex(r.index)
    ye = e.groupby(e.index.year).last(); yr = ye.pct_change(); yr.iloc[0] = ye.iloc[0] - 1
    return dict(tot=e.iloc[-1] - 1, cagr=cagr, vol=r.std() * np.sqrt(252), dd=dd, cdd=cagr / abs(dd) if dd < 0 else np.nan,
                sharpe=x.mean() / x.std() * np.sqrt(252), worst=yr.min(), worst_y=int(yr.idxmin()))


def boot(x, y=None, B=10000, block=63, seed=118):
    """Bootstrap a blocchi circolari. x: eccessi giornalieri. Se y è dato: differenza di Sharpe x − y (appaiata).
    p a una coda con nulla centrata: quota di (stat* − stat) ≥ stat."""
    rng = np.random.default_rng(seed)
    x = np.asarray(x, float); n = len(x)
    nb = int(np.ceil(n / block))
    starts = rng.integers(0, n, size=(B, nb))
    ix = (starts[:, :, None] + np.arange(block)[None, None, :]).reshape(B, -1)[:, :n] % n
    if y is None:
        st = x.mean(); bs = x[ix].mean(axis=1)
    else:
        y = np.asarray(y, float)
        sh = lambda a: a.mean(axis=-1) / a.std(axis=-1)
        st = sh(x) - sh(y); bs = sh(x[ix]) - sh(y[ix])
    return float(st), float(((bs - st) >= st).mean())
