"""v1 · voto di 17 indicatori: strategia long/short su BTC giornaliero, e confronto approfondito con W3.2.

Modulo autonomo (solo pandas/numpy), pensato per essere copiato in radar/ (per esempio radar/v1.py). Riproduce esattamente la v1
dello studio (ANALISI_BTC.md, CONFRONTO_W32.md del repo teststrategy): stessi indicatori, stesse soglie, stessi costi.

Regole (fisse, scelte sul 2018-2021; NON vanno ottimizzate):
- ogni giorno, alla chiusura UTC, 17 indicatori che seguono il trend votano +1 (long), -1 (short) o 0 (neutro);
- voto = media dei 17, da -1 a +1;
- long se voto >= +0,50; short se voto <= -0,90; uscita dal long sotto +0,25, dallo short sopra -0,25; fra le soglie si
  mantiene la posizione;
- esecuzione alla chiusura del giorno della decisione; esposizione 1x: long in spot, short sul perp con il funding reale;
  costi 0,10% per lato (commissione + slittamento).

Ingresso: DataFrame giornaliero con indice di date (UTC, solo giorni CHIUSI) e colonne open, high, low, close, volume e, se c'e',
funding (tasso giornaliero del perp; dove manca si usa 0,03% al giorno). Servono almeno ~300 giorni prima della data di inizio
del backtest per scaldare gli indicatori (SMA 200 giorni, SMA 40 settimane, OBV contro la sua media a 100 giorni).

Funzioni principali:
- evaluate(d, capital)                       stato di oggi, voto dei 17, distanze dalle soglie, storico e metriche;
- confronto(d, w32_eq, w32_trades, ...)       confronto con W3.2: metriche per periodo, anni, accordo giorno per giorno,
                                              operazioni incrociate, indicatori, combinazione 50/50, affidabilita' statistica.
"""
from __future__ import annotations

import math
from statistics import NormalDist

import numpy as np
import pandas as pd

TH_LONG, TH_SHORT, EXIT = 0.50, 0.90, 0.25
COST = 0.0010                   # per lato
FUND_DEFAULT = 0.0003           # tasso giornaliero del perp dove manca lo storico (0,01% ogni 8 ore)
START = "2018-01-01"
ND = NormalDist()
EULER = 0.5772156649

# ------------------------------------------------------------------ indicatori (identici allo studio)
sma = lambda s, n: s.rolling(n).mean()
ema = lambda s, n: s.ewm(span=n, adjust=False).mean()


def weekly(d: pd.DataFrame) -> pd.DataFrame:
    w = d.resample("W-SUN").agg({"open": "first", "high": "max", "low": "min", "close": "last", "volume": "sum"}).dropna()
    return w[w.index <= d.index[-1]]


def to_daily(s: pd.Series, d: pd.DataFrame) -> pd.Series:
    """Valore settimanale (noto alla chiusura della domenica) riportato sui giorni da quella domenica in poi."""
    return s.reindex(d.index, method="ffill")


def rsi(c, n=14):
    x = c.diff()
    up, dn = x.clip(lower=0).ewm(alpha=1 / n, adjust=False).mean(), (-x.clip(upper=0)).ewm(alpha=1 / n, adjust=False).mean()
    return 100 - 100 / (1 + up / dn)


def macd(c, f=12, s=26, g=9):
    m = ema(c, f) - ema(c, s)
    return m, ema(m, g)


def atr(d, n=14):
    c = d["close"]
    tr = pd.concat([d["high"] - d["low"], (d["high"] - c.shift()).abs(), (d["low"] - c.shift()).abs()], axis=1).max(axis=1)
    return tr.ewm(alpha=1 / n, adjust=False).mean()


def adx(d, n=14):
    up, dn = d["high"].diff(), -d["low"].diff()
    plus = pd.Series(np.where((up > dn) & (up > 0), up, 0.0), d.index)
    minus = pd.Series(np.where((dn > up) & (dn > 0), dn, 0.0), d.index)
    a = atr(d, n)
    pdi, mdi = 100 * plus.ewm(alpha=1 / n, adjust=False).mean() / a, 100 * minus.ewm(alpha=1 / n, adjust=False).mean() / a
    dx = 100 * (pdi - mdi).abs() / (pdi + mdi)
    return dx.ewm(alpha=1 / n, adjust=False).mean(), pdi, mdi


def obv(d):
    return (np.sign(d["close"].diff()).fillna(0) * d["volume"]).cumsum()


def bollinger(c, n=20, k=2.0):
    m, s = sma(c, n), c.rolling(n).std()
    return m, m + k * s, m - k * s


def donchian_state(d, n):
    """+1 dall'ultima chiusura sopra il massimo delle n barre precedenti, -1 dall'ultima sotto il minimo."""
    hi, lo = d["high"].rolling(n).max().shift(), d["low"].rolling(n).min().shift()
    s = pd.Series(np.where(d["close"] > hi, 1.0, np.where(d["close"] < lo, -1.0, np.nan)), d.index)
    return s.ffill().fillna(0.0)


def supertrend(d, n=10, k=3.0):
    a = atr(d, n)
    mid = (d["high"] + d["low"]) / 2
    ub, lb = (mid + k * a).to_numpy().copy(), (mid - k * a).to_numpy().copy()
    c = d["close"].to_numpy()
    dirn = np.ones(len(c))
    for i in range(1, len(c)):
        if not np.isfinite(ub[i - 1]):
            continue
        ub[i] = min(ub[i], ub[i - 1]) if c[i - 1] <= ub[i - 1] else ub[i]
        lb[i] = max(lb[i], lb[i - 1]) if c[i - 1] >= lb[i - 1] else lb[i]
        dirn[i] = 1 if c[i] > ub[i - 1] else -1 if c[i] < lb[i - 1] else dirn[i - 1]
    return pd.Series(dirn, d.index)


def ichimoku_state(d):
    h, l, c = d["high"], d["low"], d["close"]
    ten, kij = (h.rolling(9).max() + l.rolling(9).min()) / 2, (h.rolling(26).max() + l.rolling(26).min()) / 2
    sa, sb = ((ten + kij) / 2).shift(26), ((h.rolling(52).max() + l.rolling(52).min()) / 2).shift(26)
    top, bot = pd.concat([sa, sb], axis=1).max(axis=1), pd.concat([sa, sb], axis=1).min(axis=1)
    return pd.Series(np.where(c > top, 1.0, np.where(c < bot, -1.0, 0.0)), d.index)


# nome, famiglia, cosa significa il voto long (testo per la dashboard)
INDICATORI = [
    ("Prezzo vs SMA 200 giorni", "trend", "prezzo sopra la media a 200 giorni"),
    ("SMA 50 vs SMA 200 (golden/death cross)", "trend", "media a 50 giorni sopra quella a 200"),
    ("EMA 20 vs EMA 50", "trend", "media esponenziale a 20 giorni sopra quella a 50"),
    ("Prezzo vs SMA 40 settimane", "trend", "chiusura settimanale sopra la media a 40 settimane"),
    ("Supertrend (10, 3)", "trend", "prezzo sopra la banda del Supertrend"),
    ("Ichimoku: sopra/sotto la nuvola", "trend", "prezzo sopra la nuvola (0 dentro la nuvola)"),
    ("ADX > 25 con +DI/−DI", "trend", "trend forte (ADX > 25) con +DI sopra −DI (0 se ADX ≤ 25)"),
    ("MACD giornaliero vs segnale", "momentum", "MACD sopra la sua linea di segnale"),
    ("MACD settimanale vs segnale", "momentum", "MACD settimanale sopra la sua linea di segnale"),
    ("RSI giornaliero vs 50", "momentum", "RSI 14 giorni sopra 50"),
    ("RSI settimanale vs 50", "momentum", "RSI 14 settimane sopra 50"),
    ("Momentum a 90 giorni", "momentum", "prezzo più alto di 90 giorni fa"),
    ("Donchian 20 giorni", "rottura", "ultima rottura dei 20 giorni verso l'alto"),
    ("Donchian 55 giorni", "rottura", "ultima rottura dei 55 giorni verso l'alto"),
    ("Donchian 20 settimane", "rottura", "ultima rottura delle 20 settimane verso l'alto"),
    ("Bollinger: rottura delle bande", "rottura", "ultima uscita dalle bande di Bollinger verso l'alto"),
    ("OBV vs sua SMA 100", "volume", "volume cumulato (OBV) sopra la sua media a 100 giorni"),
]
NOMI = [x[0] for x in INDICATORI]


def signals(d: pd.DataFrame) -> pd.DataFrame:
    """Voto di ognuno dei 17 indicatori, giorno per giorno: +1, -1 o 0. Dato noto alla chiusura del giorno."""
    c, w = d["close"], weekly(d)
    wc = w["close"]
    sgn = lambda x: pd.Series(np.sign(x), x.index).fillna(0.0)
    s = pd.DataFrame(index=d.index)
    s[NOMI[0]] = sgn(c - sma(c, 200))
    s[NOMI[1]] = sgn(sma(c, 50) - sma(c, 200))
    s[NOMI[2]] = sgn(ema(c, 20) - ema(c, 50))
    s[NOMI[3]] = to_daily(sgn(wc - sma(wc, 40)), d)
    s[NOMI[4]] = supertrend(d)
    s[NOMI[5]] = ichimoku_state(d)
    a, pdi, mdi = adx(d)
    s[NOMI[6]] = np.where(a > 25, np.sign(pdi - mdi), 0.0)
    m, sg = macd(c)
    s[NOMI[7]] = sgn(m - sg)
    mw, sgw = macd(wc)
    s[NOMI[8]] = to_daily(sgn(mw - sgw), d)
    s[NOMI[9]] = sgn(rsi(c) - 50)
    s[NOMI[10]] = to_daily(sgn(rsi(wc) - 50), d)
    s[NOMI[11]] = sgn(c.pct_change(90))
    s[NOMI[12]] = donchian_state(d, 20)
    s[NOMI[13]] = donchian_state(d, 55)
    s[NOMI[14]] = to_daily(donchian_state(w, 20), d)
    _, ub, lb = bollinger(c)
    s[NOMI[15]] = pd.Series(np.where(c > ub, 1.0, np.where(c < lb, -1.0, np.nan)), d.index).ffill().fillna(0.0)
    o = obv(d)
    s[NOMI[16]] = sgn(o - sma(o, 100))
    return s.fillna(0.0)


def score(sig: pd.DataFrame) -> pd.Series:
    return sig[NOMI].mean(axis=1)


def decide(sc: pd.Series) -> pd.Series:
    """Posizione decisa alla chiusura di ogni giorno: +1 long, -1 short, 0 fuori."""
    x, out, cur = sc.to_numpy(), np.zeros(len(sc)), 0.0
    for i in range(len(x)):
        if np.isfinite(x[i]):
            if cur > 0 and x[i] < EXIT:
                cur = 0.0
            if cur < 0 and x[i] > -EXIT:
                cur = 0.0
            if cur == 0:
                cur = 1.0 if x[i] >= TH_LONG else -1.0 if x[i] <= -TH_SHORT else 0.0
        out[i] = cur
    return pd.Series(out, sc.index)


# ------------------------------------------------------------------ motore
def run(d: pd.DataFrame, pos: pd.Series, start: str = START) -> dict:
    """pos[t] decisa alla chiusura di t, attiva da t+1 (cioe' eseguita alla chiusura di t). Long in spot, short in perp con funding."""
    p = pos.shift(1).fillna(0.0).loc[start:]
    r = d["close"].pct_change().reindex(p.index).fillna(0.0)
    fund = (d["funding"] if "funding" in d else pd.Series(FUND_DEFAULT, d.index)).reindex(p.index).fillna(FUND_DEFAULT)
    turn = p.diff().abs().fillna(p.abs())
    perp = p - p.clip(lower=0, upper=1)
    ret = (p * r - turn * COST - perp * fund).clip(lower=-1.0)
    return {"equity": (1 + ret).cumprod(), "ret": ret, "pos": p}


def simulate(d: pd.DataFrame, start: str = START) -> dict:
    """Backtest completo: equity giornaliera (da 1,0), operazioni con prezzi, voto all'ingresso e all'uscita, motivo dell'uscita."""
    sig = signals(d)
    sc = score(sig)
    pos = decide(sc)
    r = run(d, pos, start)
    p, ret, c = r["pos"], r["ret"], d["close"]
    sg = np.sign(p)
    grp = (sg != sg.shift()).cumsum()
    trades = []
    for _, g in ret.groupby(grp):
        s0 = float(sg.loc[g.index[0]])
        if s0 == 0:
            continue
        d0, d1 = g.index[0] - pd.Timedelta(days=1), g.index[-1]        # giorno della decisione d'ingresso; ultimo giorno in posizione
        aperta = d1 >= p.index[-1] and pos.iloc[-1] == s0
        vin, vout = float(sc.loc[d0]), float(sc.loc[d1]) if not aperta else None
        if aperta:
            motivo = "aperta"
        elif s0 > 0:
            motivo = f"voto sceso a {vout:+.2f} (sotto +{EXIT:.2f})".replace(".", ",")
        else:
            motivo = f"voto salito a {vout:+.2f} (sopra −{EXIT:.2f})".replace(".", ",")
        trades.append({"verso": "long" if s0 > 0 else "short", "decisione": str(d0.date()), "entra": str(g.index[0].date()),
                       "esce": None if aperta else str(d1.date()), "giorni": int(len(g)), "prezzo_in": round(float(c.loc[d0]), 2),
                       "prezzo_out": round(float(c.loc[d1]), 2), "risultato": float((1 + g).prod() - 1), "voto_in": round(vin, 3),
                       "voto_out": None if vout is None else round(vout, 3), "motivo": motivo,
                       "mercato": "spot" if s0 > 0 else "perp"})
    return {"sig": sig, "score": sc, "pos_decisa": pos, "pos": p, "ret": ret, "equity": r["equity"], "trades": trades}


def metrics(eq: pd.Series, trades: list[dict] | None = None, a: str | None = None, b: str | None = None) -> dict:
    e = eq.loc[a:b].dropna()
    e = e / e.iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    x = e.pct_change().dropna()
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1) if e.iloc[-1] > 0 and yrs > 0 else float("nan")
    yr = e.groupby(e.index.year).last()
    yr = (yr / yr.shift(1).fillna(1.0) - 1)
    out = {"dal": str(e.index[0].date()), "al": str(e.index[-1].date()), "finale_10k": round(10000 * float(e.iloc[-1])), "cagr": cagr, "dd": dd,
           "mar": cagr / abs(dd) if dd < 0 else None, "sharpe": float(x.mean() / x.std() * math.sqrt(365)) if x.std() > 0 else None,
           "anno_peggiore": float(yr.min())}
    if trades is not None:
        t = [q for q in trades if q["entra"] >= out["dal"] and q["entra"] <= out["al"]]
        r = np.array([q["risultato"] for q in t])
        out |= {"operazioni": len(t), "in_guadagno": float((r > 0).mean()) if len(r) else None, "per_anno": len(t) / yrs if yrs else None,
                "media_vincenti": float(r[r > 0].mean()) if (r > 0).any() else None, "media_perdenti": float(r[r <= 0].mean()) if (r <= 0).any() else None,
                "peggiore": float(r.min()) if len(r) else None, "migliore": float(r.max()) if len(r) else None}
    return out


# ------------------------------------------------------------------ stato di oggi
def _mancano(votes: np.ndarray, target: float, verso: int) -> int:
    """Quanti indicatori devono cambiare voto perche' la media raggiunga `target` nel verso indicato (+1 sale, -1 scende)."""
    need = target * len(votes) - votes.sum() if verso > 0 else votes.sum() - target * len(votes)
    if need <= 1e-9:
        return 0
    gains = sorted(((1 - v) if verso > 0 else (v + 1)) for v in votes)[::-1]
    n, acc = 0, 0.0
    for g_ in gains:
        if acc >= need - 1e-9 or g_ <= 0:
            break
        acc += g_
        n += 1
    return n


def evaluate(d: pd.DataFrame, capital: float = 10000.0, start: str = START) -> dict:
    """Stato della v1 alla chiusura dell'ultimo giorno di `d` (solo giorni chiusi), con il dettaglio del voto e lo storico."""
    s = simulate(d, start)
    sig, sc, pos = s["sig"], s["score"], s["pos_decisa"]
    last, prev = float(pos.iloc[-1]), float(pos.iloc[-2])
    v = sig.iloc[-1][NOMI].to_numpy()
    cur = "long" if last > 0 else "short" if last < 0 else "fuori"
    evento = None
    if last != prev:
        evento = "ingresso long" if last > 0 else "ingresso short" if last < 0 else "uscita"
    giorni = int((pos.iloc[::-1] == last).cumprod().sum())
    soglie = {"long": TH_LONG, "short": -TH_SHORT, "uscita_long": EXIT, "uscita_short": -EXIT}
    if cur == "fuori":
        dist = {"per_long": _mancano(v, TH_LONG, 1), "per_short": _mancano(v, -TH_SHORT, -1)}
    elif cur == "long":
        dist = {"per_uscire": _mancano(v, EXIT - 1e-6, -1)}
    else:
        dist = {"per_uscire": _mancano(v, -EXIT + 1e-6, 1)}
    comp = [{"nome": n, "famiglia": f, "long_se": t, "voto": int(sig.iloc[-1][n]), "da": str(sig[n].ne(sig[n].shift()).cumsum().pipe(lambda g: sig[n][g == g.iloc[-1]].index[0]).date())}
            for n, f, t in INDICATORI]
    op = s["trades"][-1] if s["trades"] and s["trades"][-1]["esce"] is None else None
    out = {"data": str(d.index[-1].date()), "prezzo": float(d["close"].iloc[-1]), "voto": round(float(sc.iloc[-1]), 3),
           "voto_ieri": round(float(sc.iloc[-2]), 3), "conteggio": {"long": int((v > 0).sum()), "short": int((v < 0).sum()), "neutri": int((v == 0).sum())},
           "posizione": cur, "evento_oggi": evento, "da_giorni": giorni, "soglie": soglie, "distanze": dist, "componenti": comp,
           "capitale": round(capital), "esposizione": 1.0 if cur != "fuori" else 0.0, "controvalore": round(capital) if cur != "fuori" else 0,
           "mercato": "spot" if cur == "long" else "perp" if cur == "short" else None, "operazione_aperta": op,
           "voto_storico": {"d": [str(x.date()) for x in sc.loc[start:].index[::7]], "v": [round(float(x), 3) for x in sc.loc[start:].iloc[::7]]}}
    out["storico"] = {"operazioni": s["trades"], "m_2018": metrics(s["equity"], s["trades"]), "m_2021": metrics(s["equity"], s["trades"], "2021-01-01"),
                      "eq_d": [str(x.date()) for x in s["equity"].index], "eq": [round(float(x), 5) for x in s["equity"]]}
    return out


# ------------------------------------------------------------------ confronto con W3.2
def _psr(r: pd.Series, sr_star: float = 0.0) -> float:
    n, sr = len(r), r.mean() / r.std()
    g3, g4 = float(r.skew()), float(r.kurt()) + 3
    den = math.sqrt(max(1e-12, 1 - g3 * sr + (g4 - 1) / 4 * sr ** 2))
    return ND.cdf((sr - sr_star) * math.sqrt(n - 1) / den)


def _sr0(n_trials: int, sd_sr_annual: float = 0.5) -> float:
    """Sharpe settimanale che il migliore di N tentativi senza abilita' raggiunge per caso (dispersione annua 0,5)."""
    sd = sd_sr_annual / math.sqrt(52)
    return sd * ((1 - EULER) * ND.inv_cdf(1 - 1 / n_trials) + EULER * ND.inv_cdf(1 - 1 / (n_trials * math.e)))


def _daily_side(trades: list[dict], idx: pd.DatetimeIndex) -> pd.Series:
    """Verso giorno per giorno (+1, -1, 0) da un elenco di operazioni con entra/esce (esce None = aperta)."""
    s = pd.Series(0.0, idx)
    for t in trades:
        a, b = pd.Timestamp(t["entra"]), pd.Timestamp(t["esce"]) if t.get("esce") else idx[-1]
        s.loc[a:b] = 1.0 if t["verso"] == "long" else -1.0
    return s


def _wk(x: pd.Series, nd: int = 4) -> dict:
    y = x.resample("W-SUN").last().dropna()
    return {"d": [str(i.date()) for i in y.index], "v": [round(float(v), nd) for v in y]}


def confronto(d: pd.DataFrame, w32_eq: pd.Series, w32_trades: list[dict], start: str = START, sim: dict | None = None) -> dict:
    """Confronto approfondito v1 contro W3.2.
    w32_eq: equity giornaliera di W3.2 (qualunque scala) sullo stesso periodo; w32_trades: operazioni di W3.2 con almeno
    verso, entra, esce (None se aperta) e sul_capitale (risultato in frazione del capitale)."""
    s = sim or simulate(d, start)
    c = d["close"]
    i0 = max(pd.Timestamp(start), w32_eq.dropna().index[0])
    i1 = min(s["equity"].index[-1], w32_eq.dropna().index[-1])
    idx = pd.date_range(i0, i1, freq="D")
    ev = s["equity"].reindex(idx).ffill()
    ew = w32_eq.reindex(idx).ffill()
    rv, rw = ev.pct_change().fillna(0.0), ew.pct_change().fillna(0.0)
    eb = c.reindex(idx).ffill()
    E = {"W3.2": ew / ew.iloc[0], "v1": ev / ev.iloc[0], "50% W3.2 + 50% v1": (1 + 0.5 * rw + 0.5 * rv).cumprod(), "BTC comprato e tenuto": eb / eb.iloc[0]}
    tw = [t | {"risultato": t.get("sul_capitale", t.get("risultato"))} for t in w32_trades]
    tv = s["trades"]
    T = {"W3.2": tw, "v1": tv}
    periodi = [("Tutto", None, None), ("2018–2021 (soglie della v1 scelte qui)", None, "2021-12-31"), ("2022–2026 (mai visto dalla v1)", "2022-01-01", None),
               ("Dal 2021 (W3.2 con dati reali)", "2021-01-01", None), ("Ultimi 12 mesi", str((idx[-1] - pd.Timedelta(days=365)).date()), None)]
    met = [{"periodo": lab, "righe": {k: metrics(e, T.get(k), a, b) for k, e in E.items()}} for lab, a, b in periodi]
    anni = sorted(set(idx.year))
    yr = {k: {int(y): float(e[e.index.year == y].iloc[-1] / (e[e.index.year < y].iloc[-1] if (e.index.year < y).any() else 1.0) - 1) for y in anni} for k, e in E.items()}

    # accordo giorno per giorno: posizione attiva in ogni giorno
    pv = s["pos"].reindex(idx).fillna(0.0)
    pw = _daily_side(tw, idx)
    rb = eb.pct_change().fillna(0.0)
    stati = [("Entrambe long", (pw > 0) & (pv > 0)), ("Entrambe short", (pw < 0) & (pv < 0)), ("Entrambe fuori", (pw == 0) & (pv == 0)),
             ("Solo W3.2 in posizione", (pw != 0) & (pv == 0)), ("Solo v1 in posizione", (pw == 0) & (pv != 0)), ("Versi opposti", (pw * pv) < 0)]
    acc = []
    for lab, m in stati:
        n = int(m.sum())
        acc.append({"stato": lab, "giorni": n, "quota": n / len(idx), "btc_annuo": float((1 + rb[m]).prod() ** (365 / n) - 1) if n > 30 else None,
                    "w32_annuo": float((1 + rw[m]).prod() ** (365 / n) - 1) if n > 30 else None, "v1_annuo": float((1 + rv[m]).prod() ** (365 / n) - 1) if n > 30 else None})
    concordi = float(((np.sign(pw) == np.sign(pv))).mean())

    # operazioni incrociate
    sc = s["score"]
    x_w = []
    for t in tw:
        a = pd.Timestamp(t["entra"])
        b = pd.Timestamp(t["esce"]) if t.get("esce") else idx[-1]
        if a < idx[0]:
            continue
        sgn = 1 if t["verso"] == "long" else -1
        seg = pv.loc[a:b]
        x_w.append({"verso": t["verso"], "entra": t["entra"], "esce": t.get("esce"), "w32": t["risultato"], "voto_v1": round(float(sc.reindex([a - pd.Timedelta(days=1)], method="ffill").iloc[0]), 2),
                    "v1_all_ingresso": {1: "long", -1: "short", 0: "fuori"}[int(pv.loc[a])], "v1_stesso_verso_quota": float((np.sign(seg) == sgn).mean()),
                    "v1_nel_periodo": float((1 + rv.loc[a:b]).prod() - 1)})
    x_v = []
    for t in tv:
        a = pd.Timestamp(t["entra"])
        b = pd.Timestamp(t["esce"]) if t.get("esce") else idx[-1]
        if a < idx[0]:
            continue
        sgn = 1 if t["verso"] == "long" else -1
        seg = pw.loc[a:b]
        x_v.append({"verso": t["verso"], "entra": t["entra"], "esce": t.get("esce"), "v1": t["risultato"], "voto_in": t["voto_in"], "motivo": t["motivo"],
                    "w32_all_ingresso": {1: "long", -1: "short", 0: "fuori"}[int(pw.loc[a])], "w32_stesso_verso_quota": float((np.sign(seg) == sgn).mean()),
                    "w32_nel_periodo": float((1 + rw.loc[a:b]).prod() - 1)})

    # indicatori: accordo con W3.2 e rendimento preso da solo
    sig = s["sig"].reindex(idx).ffill()
    ind = []
    inpos = pw != 0
    for n, f, _ in INDICATORI:
        alone = run(d, s["sig"][n], start)["equity"].reindex(idx).ffill()
        ind.append({"nome": n, "famiglia": f, "accordo_con_w32": float((np.sign(sig[n][inpos]) == np.sign(pw[inpos])).mean()) if inpos.any() else None,
                    "da_solo_cagr": metrics(alone, None)["cagr"], "da_solo_dd": metrics(alone, None)["dd"], "oggi": int(s["sig"][n].iloc[-1])})

    # affidabilita' statistica (rendimenti settimanali)
    aff = {}
    for k in ("W3.2", "v1", "50% W3.2 + 50% v1"):
        r = E[k].resample("W-SUN").last().pct_change().dropna()
        aff[k] = {"sharpe_annuo": float(r.mean() / r.std() * math.sqrt(52)), "prob_sharpe_positivo": _psr(r),
                  "deflazionato_10": _psr(r, _sr0(10)), "deflazionato_100": _psr(r, _sr0(100))}
        rr = np.sort(np.array([q["risultato"] for q in T[k]]))[::-1] if k in T else None
        if rr is not None and len(rr) > 3:
            aff[k]["senza_le_3_migliori"] = float(np.prod(1 + rr[3:]))
            aff[k]["con_tutte"] = float(np.prod(1 + rr))

    mm = pd.concat([rw, rv], axis=1).resample("ME").apply(lambda z: (1 + z).prod() - 1)
    dd = {k: (e / e.cummax() - 1) for k, e in E.items()}
    return {"periodo": {"dal": str(idx[0].date()), "al": str(idx[-1].date())}, "metriche": met, "anni": yr,
            "accordo": {"stati": acc, "stesso_verso_quota": concordi, "corr_mensile": float(mm.corr().iloc[0, 1])},
            "operazioni_w32": x_w, "operazioni_v1": x_v, "indicatori": ind, "affidabilita": aff,
            "serie": {"equity": {k: _wk(e) for k, e in E.items()}, "drawdown": {k: _wk(x) for k, x in dd.items()},
                      "posizioni": {"W3.2": _wk(pw, 0), "v1": _wk(pv, 0)}},
            "lettura": ["W3.2 usa il flusso del perp e il funding; la v1 solo il prezzo e il volume spot.",
                        "Le soglie della v1 sono state scelte sul 2018–2021: il periodo 2022–2026 è l'unico in cui la v1 non ha mai visto i dati.",
                        "La v1 ha esposizione fissa 1x; W3.2 dimensiona la posizione sul rischio allo stop (25% del capitale)."]}


if __name__ == "__main__":
    import json
    import sys
    d = pd.read_csv(sys.argv[1] if len(sys.argv) > 1 else "btc_giornaliero.csv", index_col=0, parse_dates=True)
    e = evaluate(d)
    print(json.dumps({k: v for k, v in e.items() if k not in ("storico", "voto_storico")}, ensure_ascii=False, indent=1))
    m = e["storico"]["m_2018"]
    print("dal 2018:", m["finale_10k"], "$,", m["operazioni"], "operazioni, CAGR", round(m["cagr"] * 100, 1), "%, DD", round(m["dd"] * 100, 1), "%")
