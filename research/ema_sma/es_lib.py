"""ema_sma · dati, medie, stati e grammatica (nessun rendimento qui). Vedi PREREG.md."""
from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
CUT = "2026-11-15"                      # ultimo giorno dello studio (dati congelati di W3.2)
KINDS, PERS = ("EMA", "SMA"), (20, 50, 100, 200)
PERIODS = {"conferma 2018-20": ("2018-01-01", "2020-12-31"), "scoperta 2021-23": ("2021-01-01", "2023-12-31"),
           "giudizio 2024-26": ("2024-01-01", CUT)}


def ma(c: pd.Series, kind: str, n: int) -> pd.Series:
    """Unica funzione di calcolo delle medie (studio e tabelle DATI*.md). SMA: media semplice di n chiusure.
    EMA: ewm(span=n, adjust=False) dalla prima chiusura della storia; non valida (NaN) prima di n chiusure."""
    if kind == "SMA":
        return c.rolling(n, min_periods=n).mean()
    e = c.ewm(span=n, adjust=False).mean()
    e.iloc[: n - 1] = np.nan
    return e


def load_4h(cut: str | None = CUT) -> pd.DataFrame:
    a = pd.read_csv(HERE / "data" / "BTCUSDT_4h.csv.gz", index_col=0, parse_dates=True)
    return a[a.index < pd.Timestamp(cut) + pd.Timedelta(days=1)] if cut else a


def daily_from(a: pd.DataFrame, long_hist: bool = True) -> pd.DataFrame:
    """Giornaliero UTC ricostruito dal 4h; prima del 17/08/2017 la storia del repo (f_long, dal 2014) per scaldare le medie."""
    d = a.resample("1D").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    if long_hist:
        f = pd.read_csv(ROOT / "research" / "p2_nuovi" / "data" / "f_long.csv.gz", index_col=0, parse_dates=True)
        d = pd.concat([f.loc[f.index < d.index[0], ["open", "high", "low", "close"]], d])
    return d


def weekly_from(d: pd.DataFrame) -> pd.DataFrame:
    """Settimanale W-SUN, solo settimane chiuse (l'ultima deve finire di domenica)."""
    w = d.resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last"}).dropna()
    return w[w.index <= d.index[-1]]


def atr(b: pd.DataFrame, n: int = 14) -> pd.Series:
    c = b["close"]
    tr = pd.concat([b["high"] - b["low"], (b["high"] - c.shift()).abs(), (b["low"] - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def hyst(c: pd.Series, m: pd.Series, n: int) -> pd.Series:
    """Stato con isteresi: +1 dopo n chiusure consecutive sopra la media, −1 dopo n consecutive sotto, altrimenti invariato."""
    up, dn = (c > m).astype(int), (c < m).astype(int)
    ru = up.groupby((up == 0).cumsum()).cumsum()
    rd = dn.groupby((dn == 0).cumsum()).cumsum()
    s = pd.Series(np.where(ru >= n, 1.0, np.where(rd >= n, -1.0, np.nan)), c.index)
    return s.ffill().fillna(0.0)


def to4h(s: pd.Series, idx4: pd.DatetimeIndex, tf: str) -> np.ndarray:
    """Porta una serie giornaliera/settimanale sull'indice 4h: il valore della barra chiusa è noto dalla chiusura della
    candela 4h delle 20:00 (ultima del giorno / della domenica) in poi."""
    t = s.index + (pd.Timedelta(hours=20) if tf in ("1D", "1W") else pd.Timedelta(0))
    return pd.Series(s.to_numpy(), t).reindex(idx4, method="ffill").to_numpy()


REGIMES = ["G0", "G1", "G2", "G3", "G4", "G5"]
ENTRIES = ["E0", "E1", "E2"]
SIDES = ["LO", "SO", "LS", "INV"]


def exits() -> list[tuple]:
    x = [("C", tf, k, p, n) for tf in ("4h", "1D") for k in KINDS for p in PERS for n in (1, 2, 3)]
    x += [("X", tf, k, pr, 0) for tf in ("4h", "1D") for k in KINDS for pr in ((20, 50), (50, 200))]
    x += [("A", "1D", "ATR", k, 0) for k in (2, 3, 4)]
    return x


def xclass(x: tuple) -> str:
    return {"C": "C" + x[1], "X": "X", "A": "A"}[x[0]]


def grammar() -> pd.DataFrame:
    rows = []
    for s in SIDES:
        for g in REGIMES:
            for e in ENTRIES:
                for xi, x in enumerate(exits()):
                    if x[0] == "A" and (s == "INV" or (g == "G0" and e == "E0")):
                        continue
                    if s == "INV" and g == "G0":
                        continue
                    rows.append(dict(side=s, reg=g, ent=e, xi=xi, xtype=x[0], xtf=x[1], xkind=x[2], xpar=str(x[3]), xn=x[4],
                                     xclass=xclass(x), fam=f"{s}|{g}|{xclass(x)}"))
    return pd.DataFrame(rows)


if __name__ == "__main__":
    g = grammar()
    print("regole", len(g), "| uscite", len(exits()), "| famiglie", g["fam"].nunique())
    print(g.groupby("side").size().to_dict(), g.groupby("xclass").size().to_dict())
    print(g.groupby("fam").size().value_counts().to_dict())
