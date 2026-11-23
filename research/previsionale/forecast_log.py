"""Registro delle previsioni (PREREG §6d) · schema e funzioni pure che il tool potrà adottare (qui non si tocca radar/).

File proposto: data/forecast_log.csv, una riga per (date, horizon, model), solo aggiunte.
Colonne:
  made_at      istante UTC in cui la riga è stata scritta (deve precedere due_date: la previsione viene PRIMA dell'esito)
  date         giorno della chiusura su cui si basa la previsione (dati disponibili a quella chiusura)
  horizon      7 o 30 (giorni di calendario)
  model        nome e versione del modello (es. "M4-v1")
  train_until  ultima etichetta usata nell'addestramento (prova dell'embargo: train_until + horizon ≤ date)
  p_up         probabilità che close(date + horizon) > close(date)
  call         "su" (p > 55%), "giu" (p < 45%), "incerto"
  close        chiusura di `date`
  due_date     date + horizon
  --- compilate UNA volta a scadenza da score(), mai prima e mai riscritte ---
  close_due, ret, outcome (1 = salito), correct (1/0, vuoto se incerto), brier ((p_up − outcome)²), scored_at

Regole: una riga già presente non si riscrive mai (né p_up né l'esito); una previsione scritta dopo la scadenza non vale
(made_at ≥ due_date → rifiutata); il punteggio usa solo chiusure definitive.
"""
from __future__ import annotations

import pandas as pd

COLS = ["made_at", "date", "horizon", "model", "train_until", "p_up", "call", "close", "due_date",
        "close_due", "ret", "outcome", "correct", "brier", "scored_at"]
LO, HI = 0.45, 0.55


def empty() -> pd.DataFrame:
    return pd.DataFrame(columns=COLS)


def call_of(p: float) -> str:
    return "su" if p > HI else ("giu" if p < LO else "incerto")


def add(log: pd.DataFrame, *, made_at: str, date: str, horizon: int, model: str, train_until: str, p_up: float, close: float) -> pd.DataFrame:
    """Aggiunge una previsione. Pura: ritorna un nuovo frame. Idempotente: se (date, horizon, model) esiste già, il registro
    torna invariato (la prima previsione scritta è quella che vale)."""
    due = (pd.Timestamp(date) + pd.Timedelta(days=int(horizon))).strftime("%Y-%m-%d")
    if pd.Timestamp(made_at).tz_localize(None) >= pd.Timestamp(due):
        raise ValueError("previsione scritta dopo la scadenza: non registrabile")
    if not 0.0 <= p_up <= 1.0:
        raise ValueError("p_up fuori da [0, 1]")
    dup = (log["date"] == date) & (log["horizon"].astype("Int64") == int(horizon)) & (log["model"] == model)
    if len(log) and dup.any():
        return log.copy()
    row = {c: None for c in COLS}
    row.update(made_at=made_at, date=date, horizon=int(horizon), model=model, train_until=train_until,
               p_up=round(float(p_up), 4), call=call_of(p_up), close=float(close), due_date=due)
    return pd.concat([log, pd.DataFrame([row], columns=COLS)], ignore_index=True)


def score(log: pd.DataFrame, closes: pd.Series, now: str) -> pd.DataFrame:
    """Compila l'esito delle righe scadute e non ancora valutate. `closes`: chiusure definitive indicizzate per data.
    Pura; le righe già valutate non cambiano."""
    out = log.copy()
    cl = closes.copy()
    cl.index = pd.to_datetime(cl.index).strftime("%Y-%m-%d")
    for i, r in out.iterrows():
        if pd.notna(r["outcome"]) or r["due_date"] not in cl.index or pd.Timestamp(r["due_date"]) >= pd.Timestamp(now).tz_localize(None).normalize():
            continue
        cd = float(cl[r["due_date"]])
        o = int(cd > float(r["close"]))
        out.loc[i, ["close_due", "ret", "outcome", "brier", "scored_at"]] = [cd, cd / float(r["close"]) - 1, o,
                                                                           round((float(r["p_up"]) - o) ** 2, 4), now]
        if r["call"] != "incerto":
            out.loc[i, "correct"] = int((r["call"] == "su") == bool(o))
    return out


def summary(log: pd.DataFrame, last: int | None = None) -> pd.DataFrame:
    """Punteggio per orizzonte sulle previsioni valutate (ultime `last` se indicato): n, copertura, % corrette fuori dalla
    fascia incerta, Brier e Brier di "50%" (0,25) come riferimento."""
    d = log[log["outcome"].notna()]
    rows = []
    for h, g in d.groupby("horizon"):
        g = g.sort_values("date").tail(last) if last else g
        c = g[g["call"] != "incerto"]
        rows.append(dict(horizon=int(h), n=len(g), copertura=len(c) / len(g), corrette=c["correct"].astype(float).mean() if len(c) else float("nan"),
                         brier=g["brier"].astype(float).mean(), brier_50=0.25, freq_su=g["outcome"].astype(float).mean()))
    return pd.DataFrame(rows)


if __name__ == "__main__":   # esempio d'uso e controllo delle regole
    lg = empty()
    lg = add(lg, made_at="2026-11-16T00:10:00Z", date="2026-11-15", horizon=7, model="M4-v1", train_until="2026-11-08", p_up=0.57, close=64000.0)
    lg = add(lg, made_at="2026-11-16T00:10:00Z", date="2026-11-15", horizon=30, model="M4-v1", train_until="2026-10-16", p_up=0.52, close=64000.0)
    lg2 = add(lg, made_at="2026-11-17T00:10:00Z", date="2026-11-15", horizon=7, model="M4-v1", train_until="2026-11-08", p_up=0.99, close=64000.0)
    assert lg2.equals(lg), "una previsione già scritta non si riscrive"
    px = pd.Series({"2026-11-15": 64000.0, "2026-11-22": 61000.0})
    s1 = score(lg, px, now="2026-11-22T12:00:00Z")
    assert s1["outcome"].isna().all(), "il giorno della scadenza non è ancora chiuso"
    s2 = score(lg, px, now="2026-11-23T00:10:00Z")
    assert s2.loc[0, "outcome"] == 0 and s2.loc[0, "correct"] == 0 and pd.isna(s2.loc[1, "outcome"])
    assert score(s2, px * 2, now="2026-11-24T00:10:00Z").loc[0, "outcome"] == 0, "un esito scritto non cambia"
    try:
        add(lg, made_at="2026-11-23T00:00:00Z", date="2026-11-15", horizon=7, model="X", train_until="", p_up=0.5, close=1.0)
        raise AssertionError("doveva rifiutare")
    except ValueError:
        pass
    print(s2.to_string())
    print(summary(s2).to_string())
