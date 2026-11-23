"""ema_sma · motore barra per barra a 4h, tutte le regole insieme (vettoriale sulle regole). Vedi PREREG.md §3–4."""
from __future__ import annotations
import numpy as np, pandas as pd
import es_lib as L

FEE_SPOT, FEE_PERP, SLIP = 0.001, 0.0005, 0.001
START = "2018-01-01"


def funding_daily() -> pd.Series:
    f = pd.read_csv(L.ROOT / "research" / "p2_nuovi" / "data" / "f_long.csv.gz", index_col=0, parse_dates=True)
    return f["funding"].fillna(0.0)


def signals(a: pd.DataFrame) -> dict:
    """Matrici dei segnali sull'indice 4h (valori noti alla chiusura di ogni candela)."""
    idx = a.index
    d = L.daily_from(a); w = L.weekly_from(d)
    c4, cd, cw = a["close"], d["close"], w["close"]
    mad = {(k, p): L.ma(cd, k, p) for k in L.KINDS for p in L.PERS}
    ma4 = {(k, p): L.ma(c4, k, p) for k in L.KINDS for p in L.PERS}
    sg = lambda x: np.sign(x).fillna(0.0)  # noqa: E731
    G = [pd.Series(1.0, cd.index), sg(cd - mad["SMA", 200]), sg(cd - mad["EMA", 200]), sg(mad["SMA", 50] - mad["SMA", 200]),
         sg(cw - L.ma(cw, "EMA", 20)), sg(cw - L.ma(cw, "SMA", 40))]
    Gm = np.column_stack([L.to4h(g, idx, "1W" if j >= 4 else "1D") for j, g in enumerate(G)])
    GL, GS = Gm > 0, Gm < 0
    GL[:, 0] = GS[:, 0] = True
    e20, e50 = mad["EMA", 20], mad["EMA", 50]
    rl = ((d["low"] <= e50).astype(float).rolling(3).max() > 0) & (cd > e50)
    rs = ((d["high"] >= e50).astype(float).rolling(3).max() > 0) & (cd < e50)
    one = pd.Series(1.0, cd.index)
    EL = np.column_stack([L.to4h(x.astype(float), idx, "1D") for x in (one, cd > e20, rl)]) > 0
    ES = np.column_stack([L.to4h(x.astype(float), idx, "1D") for x in (one, cd < e20, rs)]) > 0
    cols = []
    for x in L.exits():
        if x[0] == "C":
            s = L.hyst(c4, ma4[x[2], x[3]], x[4]).to_numpy() if x[1] == "4h" else L.to4h(L.hyst(cd, mad[x[2], x[3]], x[4]), idx, "1D")
        elif x[0] == "X":
            m = ma4 if x[1] == "4h" else mad
            s = sg(m[x[2], x[3][0]] - m[x[2], x[3][1]])
            s = s.to_numpy() if x[1] == "4h" else L.to4h(s, idx, "1D")
        else:
            s = np.zeros(len(idx))
        cols.append(np.nan_to_num(s))
    FX = np.column_stack(cols).astype(np.int8)
    atrd = L.to4h(L.atr(d), idx, "1D"); atrw = L.to4h(L.atr(w), idx, "1W")
    fu = L.to4h(funding_daily(), idx, "4h"); fu = np.nan_to_num(pd.Series(fu, idx).ffill().to_numpy()) / 6.0
    last = np.r_[idx.normalize()[1:] != idx.normalize()[:-1], True]      # ultima candela del giorno
    return dict(idx=idx, O=a["open"].to_numpy(), H=a["high"].to_numpy(), Lo=a["low"].to_numpy(), C=c4.to_numpy(), GL=GL, GS=GS,
                EL=EL, ES=ES, FX=FX, atrd=atrd, atrw=atrw, fu=fu, last=last, daily=d, weekly=w)


def rule_arrays(g: pd.DataFrame) -> dict:
    xs = L.exits()
    return dict(gi=g["reg"].str[1].astype(int).to_numpy(), ei=g["ent"].str[1].astype(int).to_numpy(), xi=g["xi"].to_numpy(),
                isA=(g["xtype"] == "A").to_numpy(), k=np.array([xs[i][3] if xs[i][0] == "A" else 0.0 for i in g["xi"]], float),
                aL=g["side"].isin(["LO", "LS", "INV"]).to_numpy(), aS=g["side"].isin(["SO", "LS", "INV"]).to_numpy(),
                inv=(g["side"] == "INV").to_numpy())


def new_state(n: int) -> dict:
    z = lambda v=0.0: np.full(n, v)  # noqa: E731
    return dict(pos=np.zeros(n, int), eq=z(1.0), cash=z(1.0), qty=z(), pxe=z(), eq0=z(1.0), stop=z(np.nan), ib=np.zeros(n, int),
                pL=np.ones(n, bool), pS=np.ones(n, bool), tgt=np.full(n, 9), sstop=z(np.nan), sexpo=z(1.0), first=True)


def run(S: dict, R: dict, i0: int, i1: int, st: dict | None = None, cap: bool = False):
    """Simula le barre [i0, i1). Ritorna (equity a fine giornata [giorni × regole], date, trade, stato)."""
    n = len(R["gi"]); ar = np.arange(n)
    st = {k: (v.copy() if isinstance(v, np.ndarray) else v) for k, v in (st or new_state(n)).items()}
    pos, eq, cash, qty, pxe, eq0, stop, ib, pL, pS, tgt, sstop, sexpo = (st[k] for k in
        ("pos", "eq", "cash", "qty", "pxe", "eq0", "stop", "ib", "pL", "pS", "tgt", "sstop", "sexpo"))
    O, H, Lo, C, fu = S["O"], S["H"], S["Lo"], S["C"], S["fu"]
    gi, ei, xi, isA, k, aL, aS, inv = (R[x] for x in ("gi", "ei", "xi", "isA", "k", "aL", "aS", "inv"))
    hasstop = isA | cap
    E, days, T = [], [], []

    def close(m, px, i):
        lg = m & (pos > 0); sh = m & (pos < 0)
        eq[lg] = cash[lg] + qty[lg] * px[lg] * (1 - SLIP) * (1 - FEE_SPOT)
        pxs = px[sh] * (1 + SLIP)
        eq[sh] = cash[sh] + qty[sh] * (pxe[sh] - pxs) - qty[sh] * pxs * FEE_PERP
        j = np.flatnonzero(m)
        if len(j):
            T.append(np.column_stack([j, ib[j], np.full(len(j), i), pos[j], eq[j] / eq0[j] - 1]))
        pos[m] = 0; qty[m] = 0.0; cash[m] = eq[m]; stop[m] = np.nan

    for i in range(i0, i1):
        o = np.full(n, O[i])
        ch = (tgt != 9) & (tgt != pos)
        if ch.any():
            close(ch & (pos != 0), o, i)
            el = ch & (tgt == 1); es = ch & (tgt == -1)
            eq0[el | es] = eq[el | es]; ib[el | es] = i
            px = O[i] * (1 + SLIP)
            qty[el] = sexpo[el] * eq[el] * (1 - FEE_SPOT) / px; cash[el] = eq[el] * (1 - sexpo[el]); pxe[el] = px
            px = O[i] * (1 - SLIP)
            qty[es] = sexpo[es] * eq[es] / px; cash[es] = eq[es] - qty[es] * px * FEE_PERP; pxe[es] = px
            pos[el] = 1; pos[es] = -1
            stop[el | es] = sstop[el | es]
        tgt[:] = 9
        hl = hasstop & (pos > 0) & (Lo[i] <= stop); hs = hasstop & (pos < 0) & (H[i] >= stop)
        if hl.any():
            close(hl, np.minimum(o, stop), i)
        if hs.any():
            close(hs, np.maximum(o, stop), i)
        sh = pos < 0
        cash[sh] += qty[sh] * C[i] * fu[i]
        eq = np.where(pos > 0, cash + qty * C[i], np.where(sh, cash + qty * (pxe - C[i]), eq))
        if S["last"][i]:
            E.append(eq.astype(np.float32)); days.append(S["idx"][i].normalize())
        a_ = S["atrd"][i]
        tl = isA & (pos > 0); ts = isA & (pos < 0)
        stop[tl] = np.maximum(stop[tl], C[i] - k[tl] * a_); stop[ts] = np.minimum(stop[ts], C[i] + k[ts] * a_)
        s_ = S["FX"][i, xi]
        cL = S["GL"][i, gi] & S["EL"][i, ei] & ((s_ == 1) | isA)
        cS = np.where(inv, s_ == -1, S["GS"][i, gi] & S["ES"][i, ei] & ((s_ == -1) | isA))
        t = pos.copy()
        t[(pos > 0) & ~isA & (s_ == -1)] = 0
        t[(pos < 0) & ~isA & (s_ == 1)] = 0
        t[cL & ~pL & aL & (pos != 1)] = 1
        t[cS & ~pS & aS & (pos != -1)] = -1
        pL[:] = cL; pS[:] = cS
        tgt[:] = np.where(t != pos, t, 9)
        d_ = np.where(isA, k * a_, np.inf)
        if cap:
            d_ = np.minimum(d_, 2.5 * S["atrw"][i]); sexpo[:] = min(1.0, 0.25 / (2.5 * S["atrw"][i] / C[i]))
        sstop[:] = np.where(t == 1, C[i] - d_, np.where(t == -1, C[i] + d_, np.nan))
    st.update(pos=pos, eq=eq, cash=cash, qty=qty, pxe=pxe, eq0=eq0, stop=stop, ib=ib, pL=pL, pS=pS, tgt=tgt, sstop=sstop, sexpo=sexpo)
    j = np.flatnonzero(pos != 0)                                   # posizioni aperte: contate alla chiusura finale
    To = np.column_stack([j, ib[j], np.full(len(j), i1 - 1), pos[j], eq[j] / eq0[j] - 1]) if len(j) else np.zeros((0, 5))
    Tc = np.vstack(T) if T else np.zeros((0, 5))
    return np.vstack(E), pd.DatetimeIndex(days), np.vstack([Tc, To]), st


def metrics(E: np.ndarray, days: pd.DatetimeIndex, T: np.ndarray, idx: pd.DatetimeIndex, a: str, b: str, n: int) -> pd.DataFrame:
    """Metriche per periodo [a, b] sulle fette della curva continua (PREREG §4)."""
    m = (days >= a) & (days <= b); j0 = np.flatnonzero(m)[0]
    base = E[j0 - 1] if j0 > 0 else np.ones(E.shape[1], np.float32)
    e = np.vstack([base, E[m]]).astype(float) / base
    yrs = ((pd.Timestamp(b) - pd.Timestamp(a)).days + 1) / 365.25
    fin = e[-1]; cagr = fin ** (1 / yrs) - 1
    dd = (e / np.maximum.accumulate(e, axis=0) - 1).min(axis=0)
    out = pd.DataFrame(dict(fin=fin * 10000, cagr=cagr, dd=dd, S=np.where(dd < 0, cagr / np.abs(np.minimum(dd, -1e-9)), np.where(cagr > 0, 99.0, 0.0))))
    tb = idx[T[:, 1].astype(int)]
    tm = (tb >= a) & (tb < pd.Timestamp(b) + pd.Timedelta(days=1))
    r, p = T[tm, 0].astype(int), T[tm, 4]
    out["n"] = np.bincount(r, minlength=n); out["wins"] = np.bincount(r, weights=(p > 0).astype(float), minlength=n)
    out["wr"] = out["wins"] / out["n"].replace(0, np.nan)
    # senza i 2 trade migliori del periodo
    df = pd.DataFrame(dict(r=r, p=p)).sort_values(["r", "p"], ascending=[True, False])
    top = df.groupby("r").head(2).assign(f=lambda x: 1 + x["p"]).groupby("r")["f"].prod().reindex(range(n)).fillna(1.0).to_numpy()
    out["fin_no2"] = out["fin"] / top
    return out


def bh(S: dict, a: str, b: str) -> dict:
    d = S["daily"]; x = d[(d.index >= a) & (d.index <= b)]
    e = np.r_[1.0, x["close"].to_numpy() / (x["open"].iloc[0] * (1 + SLIP)) * (1 - FEE_SPOT)]
    yrs = ((pd.Timestamp(b) - pd.Timestamp(a)).days + 1) / 365.25
    cagr = e[-1] ** (1 / yrs) - 1; dd = (e / np.maximum.accumulate(e) - 1).min()
    return dict(fin=e[-1] * 10000, cagr=cagr, dd=dd, S=cagr / abs(dd), n=1)


def permute(a: pd.DataFrame, p0: str, p1: str, rng: np.random.Generator, block: int = 120) -> pd.DataFrame:
    """Serie con il periodo [p0, p1] rimescolato a blocchi (rapporti O/H/L/C sulla chiusura precedente); il resto reale."""
    i0 = a.index.searchsorted(pd.Timestamp(p0)); i1 = a.index.searchsorted(pd.Timestamp(p1) + pd.Timedelta(days=1))
    v = a[["open", "high", "low", "close"]].to_numpy()
    r = v[i0:i1] / v[i0 - 1:i1 - 1, 3:4]
    nb = int(np.ceil(len(r) / block)); order = rng.permutation(nb)
    r = np.vstack([r[j * block:(j + 1) * block] for j in order])
    c = v[i0 - 1, 3] * np.cumprod(r[:, 3]); prev = np.r_[v[i0 - 1, 3], c[:-1]]
    out = a.iloc[:i1].copy()
    out.iloc[i0:i1, [out.columns.get_loc(x) for x in ("open", "high", "low", "close")]] = r * prev[:, None]
    return out
