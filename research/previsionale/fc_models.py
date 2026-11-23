"""Previsionale · modelli (PREREG §3–4), solo numpy/pandas. Funzioni pure, riusabili dal tool.

M1 logistica L2 sulle variabili di prezzo, M2 logistica L2 su tutte, M3 insieme di ceppi a terzili, M4 media.
walk_forward(): riaddestramento mensile espansivo con embargo h (entra solo l'etichetta già nota).
"""
from __future__ import annotations

import numpy as np
import pandas as pd

from fc_data import ALL, PRICE, labels

LAMS = (1.0, 10.0, 100.0, 1000.0, 10000.0)
KS = (20.0, 100.0, 500.0)
TRAIN_START = "2015-01-01"
EPS = 1e-6


def _sig(z):
    return 1 / (1 + np.exp(-np.clip(z, -30, 30)))


def logit(p):
    p = np.clip(p, EPS, 1 - EPS)
    return np.log(p / (1 - p))


def logloss(y, p) -> float:
    p = np.clip(p, EPS, 1 - EPS)
    return float(-np.mean(y * np.log(p) + (1 - y) * np.log(1 - p)))


# ------------------------------------------------------------------ logistica L2 (IRLS)
def scaler(X: np.ndarray) -> tuple[np.ndarray, np.ndarray]:
    mu, sd = np.nanmean(X, axis=0), np.nanstd(X, axis=0)
    mu = np.where(np.isfinite(mu), mu, 0.0)
    sd = np.where(np.isfinite(sd) & (sd > 0), sd, 1.0)
    return mu, sd


def scale(X: np.ndarray, mu: np.ndarray, sd: np.ndarray) -> np.ndarray:
    return np.nan_to_num(np.clip((X - mu) / sd, -3, 3), nan=0.0)   # mancante = media


def fit_logit(Z: np.ndarray, y: np.ndarray, lam: float, it: int = 50) -> np.ndarray:
    """Z standardizzata (n × k). Ritorna [intercetta, beta...]; penalità lam·‖beta‖² (intercetta libera)."""
    A = np.column_stack([np.ones(len(Z)), Z])
    P = 2 * lam * np.eye(A.shape[1])
    P[0, 0] = 0.0
    w = np.zeros(A.shape[1])
    w[0] = logit(np.mean(y))
    for _ in range(it):
        p = _sig(A @ w)
        g = A.T @ (p - y) + P @ w
        Hs = (A * (p * (1 - p))[:, None]).T @ A + P + 1e-9 * np.eye(A.shape[1])
        step = np.linalg.solve(Hs, g)
        w = w - step
        if np.max(np.abs(step)) < 1e-8:
            break
    return w


def pred_logit(w: np.ndarray, Z: np.ndarray) -> np.ndarray:
    return _sig(w[0] + Z @ w[1:])


# ------------------------------------------------------------------ ceppi a terzili
def fit_stumps(X: np.ndarray, y: np.ndarray, k: float) -> dict:
    base = float(np.mean(y))
    edges, lo = [], []
    for j in range(X.shape[1]):
        v = X[:, j]
        ok = np.isfinite(v)
        if ok.sum() < 90:
            edges.append(None)
            lo.append(None)
            continue
        e = np.quantile(v[ok], [1 / 3, 2 / 3])
        b = np.digitize(v[ok], e)
        pj = np.array([(y[ok][b == q].sum() + k * base) / ((b == q).sum() + k) for q in range(3)])
        edges.append(e)
        lo.append(logit(pj) - logit(base))
    return {"base": base, "edges": edges, "lo": lo}


def pred_stumps(m: dict, X: np.ndarray) -> np.ndarray:
    s, n = np.zeros(len(X)), np.zeros(len(X))
    for j, e in enumerate(m["edges"]):
        if e is None:
            continue
        v = X[:, j]
        ok = np.isfinite(v)
        s[ok] += m["lo"][j][np.digitize(v[ok], e)]
        n[ok] += 1
    return _sig(logit(m["base"]) + s / np.maximum(n, 1))


# ------------------------------------------------------------------ addestramento a una data
def train(x: pd.DataFrame, y: pd.Series, h: int, D: pd.Timestamp) -> dict:
    """Modelli stimati con le sole righe t ≥ TRAIN_START con t + h ≤ D − 1 (etichetta nota prima di D)."""
    m = (x.index >= TRAIN_START) & (x.index + pd.Timedelta(days=h) <= D - pd.Timedelta(days=1)) & y.notna().to_numpy()
    m &= x[PRICE].notna().all(axis=1).to_numpy()
    X, yy = x.loc[m, ALL].to_numpy(float), y[m].to_numpy(float)
    n = len(yy)
    i70 = int(n * 0.7)
    tr, va = slice(0, max(i70 - h, 1)), slice(i70, n)          # embargo h fra stima e validazione interna
    ip = [ALL.index(c) for c in PRICE]
    out = {"n": n, "base": float(yy.mean()), "until": str(x.index[m][-1].date())}
    for name, cols in (("m1", ip), ("m2", list(range(len(ALL))))):
        mu, sd = scaler(X[tr][:, cols])
        Ztr, Zva = scale(X[tr][:, cols], mu, sd), scale(X[va][:, cols], mu, sd)
        ll = [logloss(yy[va], pred_logit(fit_logit(Ztr, yy[tr], lam), Zva)) for lam in LAMS]
        lam = LAMS[int(np.argmin(ll))]
        mu, sd = scaler(X[:, cols])
        out[name] = {"cols": cols, "mu": mu, "sd": sd, "lam": lam, "w": fit_logit(scale(X[:, cols], mu, sd), yy, lam)}
    ll = [logloss(yy[va], pred_stumps(fit_stumps(X[tr], yy[tr], k), X[va])) for k in KS]
    k = KS[int(np.argmin(ll))]
    out["m3"] = dict(fit_stumps(X, yy, k), k=k)
    return out


def predict(mod: dict, X: np.ndarray) -> np.ndarray:
    """X: righe con le 12 variabili nell'ordine ALL. Ritorna colonne p1, p2, p3, p4."""
    p = []
    for name in ("m1", "m2"):
        a = mod[name]
        p.append(pred_logit(a["w"], scale(X[:, a["cols"]], a["mu"], a["sd"])))
    p.append(pred_stumps(mod["m3"], X))
    p.append(np.mean(p, axis=0))
    return np.column_stack(p)


def walk_forward(x: pd.DataFrame, h: int, start: str = "2018-01-01", static: str | None = None) -> tuple[pd.DataFrame, pd.DataFrame]:
    """Previsioni giornaliere da `start` all'ultima riga. static="2021-01-01": un solo addestramento a quella data.
    Ritorna (previsioni con y, storia dei coefficienti e degli iperparametri a ogni riaddestramento)."""
    y = labels(x, h)
    ok = x[PRICE].notna().all(axis=1)
    days = x.index[(x.index >= start) & ok.to_numpy()]
    months = pd.date_range(days[0].replace(day=1), days[-1], freq="MS")
    rows, hist, mod = [], [], None
    if static:
        mod = train(x, y, h, pd.Timestamp(static))
    for D in months:
        if not static:
            mod = train(x, y, h, D)
            rec = {"D": D, "n": mod["n"], "base": mod["base"], "lam1": mod["m1"]["lam"], "lam2": mod["m2"]["lam"], "k3": mod["m3"]["k"]}
            rec.update({f"b_{c}": mod["m2"]["w"][1 + i] for i, c in enumerate(ALL)})
            rec.update({f"b1_{c}": mod["m1"]["w"][1 + i] for i, c in enumerate(PRICE)})
            hist.append(rec)
        dd = days[(days >= D) & (days < D + pd.offsets.MonthBegin(1))]
        if not len(dd):
            continue
        P = predict(mod, x.loc[dd, ALL].to_numpy(float))
        r = pd.DataFrame(P, index=dd, columns=["p1", "p2", "p3", "p4"])
        r["p0"] = mod["base"]
        rows.append(r)
    out = pd.concat(rows)
    out["y"] = y.reindex(out.index)
    return out, pd.DataFrame(hist).set_index("D") if hist else pd.DataFrame()


# ------------------------------------------------------------------ ricalibrazione di Platt sugli errori passati
def platt_fit(p: np.ndarray, y: np.ndarray) -> np.ndarray:
    return fit_logit(logit(p)[:, None], y, 1e-6)


def recalibrate(pr: pd.DataFrame, col: str, h: int, window: int | None, min_days: int = 365, start: str = "2021-01-01") -> pd.Series:
    """A ogni primo del mese D: Platt sulle previsioni fuori campione già risolte (t + h ≤ D − 1), finestra espansiva
    (window=None) o ultimi `window` giorni. Prima di `min_days` giorni risolti la probabilità resta invariata (NaN = non attiva)."""
    out = pd.Series(np.nan, index=pr.index)
    for D in pd.date_range(pd.Timestamp(start).replace(day=1), pr.index[-1], freq="MS"):
        past = pr[(pr.index + pd.Timedelta(days=h) <= D - pd.Timedelta(days=1)) & pr["y"].notna()]
        if window:
            past = past[past.index >= D - pd.Timedelta(days=window + h)]
        if len(past) < min_days:
            continue
        w = platt_fit(past[col].to_numpy(), past["y"].to_numpy())
        m = (pr.index >= D) & (pr.index < D + pd.offsets.MonthBegin(1))
        out[m] = _sig(w[0] + w[1] * logit(pr.loc[m, col].to_numpy()))
    return out
