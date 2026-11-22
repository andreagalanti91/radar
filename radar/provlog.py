"""Registro domenicale "provvisori vs definitivi" della decisione W3.1 (solo registro: non cambia segnali né posizione).

Alla decisione settimanale (primo giro con i dati fino alla domenica UTC) salva in data/provlog.csv i valori usati per
decidere: flusso perp (weekly.live_flow) con i 3 pf14z giornalieri che lo compongono e la loro fonte, funding medio 7g e
fonte, chiusura, EMA 21, SMA 40, esito di weekly._decide e margini dalle soglie (flusso da 0, funding da 0,0009 / −0,0003).
Fonte "okx" = provvisoria: almeno un giorno della finestra (14 giorni per il pf14z, 7 per il funding) viene da OKX e non
ancora dall'archivio Binance. A ogni giro successivo, quando la finestra è tutta Binance, la riga si completa con il valore
definitivo e lo scarto; con flusso e funding definitivi si ricalcola l'esito e si segnala se la decisione sarebbe cambiata.
Il perp definitivo arriva di solito il giorno dopo, il funding definitivo solo a inizio del mese successivo (archivio mensile).
"""
from __future__ import annotations

from pathlib import Path

import numpy as np
import pandas as pd

from . import weekly

FILE = "provlog.csv"
PF_WIN, FUND_WIN = 14, 7
COLS = ["date", "logged_at", "late", "side", "close", "ema21", "sma40",
        "flow_p", "pf1_date", "pf1_p", "pf1_src", "pf2_date", "pf2_p", "pf2_src", "pf3_date", "pf3_p", "pf3_src",
        "fund7_p", "fund7_src", "decision_p", "m_flow_p", "m_fhot_p", "m_fcold_p",
        "flow_d", "pf1_d", "pf2_d", "pf3_d", "flow_d_at", "d_flow", "fund7_d", "fund7_d_at", "d_fund7",
        "decision_d", "changed"]


def _f(x, nd: int = 6):
    return None if x is None or pd.isna(x) else round(float(x), nd)


def window_src(src: pd.Series | None, day: pd.Timestamp, n: int) -> str:
    """'binance' se tutti gli n giorni fino a `day` vengono dall'archivio Binance, altrimenti 'okx' (provvisorio).
    Un giorno assente o senza etichetta conta come provvisorio."""
    if src is None or not len(src):
        return "okx"
    days = pd.date_range(day - pd.Timedelta(days=n - 1), day, freq="D")
    s = src.reindex(days)
    return "binance" if bool((s == "binance").all()) else "okx"


def side_at(trades: list[dict], day: str) -> int:
    """Posizione W3 alla chiusura di `day` (prima della decisione): trade entrato entro `day` e non ancora uscito."""
    for t in trades or []:
        if t.get("entry") and t["entry"] <= day and (not t.get("exit") or t["exit"] > day):
            return 1 if t.get("side") == "long" else -1
    return 0


def decision_text(wk: pd.Series, side: int) -> str:
    d = weekly._decide(wk, side)
    if not d:
        return "nessuna"
    return f"ingresso {'long' if d[1] > 0 else 'short'}" if d[0] == "enter" else f"uscita {d[1]}"


def decision_sunday(last_day: pd.Timestamp) -> pd.Timestamp:
    """Ultima domenica (chiusura settimanale) non successiva a `last_day`."""
    return (last_day - pd.Timedelta(days=(last_day.dayofweek + 1) % 7)).normalize()


def values(f: pd.DataFrame, perp_src: pd.Series | None, fund_src: pd.Series | None, day: pd.Timestamp) -> dict:
    """Valori della decisione della domenica `day` con i dati attuali (flusso, 3 pf14z e fonti, funding 7g e fonte)."""
    w = weekly.weekly_bars(f)
    wk = w.loc[day]
    i = f.index.get_loc(day)
    pf_days = f.index[max(0, i - weekly.FLOW_N):i]          # live_flow: media dei pf14z dei 3 giorni prima della domenica
    out = {"wk": wk, "flow": _f(wk["flow"]), "fund7": _f(wk["fund7"], 8), "close": _f(wk["close"], 2),
           "ema21": _f(wk["ema21"], 2), "sma40": _f(wk["sma"], 2), "pf": [],
           "fund7_src": window_src(fund_src, day, FUND_WIN)}
    for d in pf_days:
        out["pf"].append({"date": str(d.date()), "v": _f(f.at[d, "pf14z"]), "src": window_src(perp_src, d, PF_WIN)})
    vals = [p["v"] for p in out["pf"] if p["v"] is not None]
    if vals and out["flow"] is not None and abs(np.mean(vals) - out["flow"]) > 1e-4:
        print(f"[provlog] controllo: flusso {out['flow']} diverso dalla media dei pf14z {np.mean(vals):.6f}")
    out["flow_def"] = len(out["pf"]) == weekly.FLOW_N and all(p["src"] == "binance" and p["v"] is not None for p in out["pf"])
    out["fund_def"] = out["fund7_src"] == "binance" and out["fund7"] is not None
    return out


def _read(path: Path) -> pd.DataFrame:
    if not path.exists():
        return pd.DataFrame(columns=COLS)
    df = pd.read_csv(path, dtype={"date": str, "pf1_date": str, "pf2_date": str, "pf3_date": str, "logged_at": str,
                                  "flow_d_at": str, "fund7_d_at": str, "decision_p": str, "decision_d": str})
    for c in COLS:
        if c not in df:
            df[c] = None
    return df[COLS].astype(object).where(df[COLS].notna(), None)


def new_row(v: dict, day: pd.Timestamp, side: int, now: pd.Timestamp, late: bool) -> dict:
    r = {c: None for c in COLS}
    r.update(date=str(day.date()), logged_at=str(now.floor("s")), late=bool(late), side=side, close=v["close"],
             ema21=v["ema21"], sma40=v["sma40"], flow_p=v["flow"], fund7_p=v["fund7"], fund7_src=v["fund7_src"],
             decision_p=decision_text(v["wk"], side),
             m_flow_p=v["flow"], m_fhot_p=_f(v["fund7"] - weekly.FUND_HOT, 8) if v["fund7"] is not None else None,
             m_fcold_p=_f(v["fund7"] - weekly.FUND_COLD, 8) if v["fund7"] is not None else None)
    for k, p in enumerate(v["pf"], 1):
        r.update({f"pf{k}_date": p["date"], f"pf{k}_p": p["v"], f"pf{k}_src": p["src"]})
    return r


def complete(r: dict, v: dict, now: pd.Timestamp) -> bool:
    """Completa una riga con i valori definitivi disponibili; True se è cambiato qualcosa."""
    ch = False
    if r.get("flow_d") is None and v["flow_def"]:
        r.update(flow_d=v["flow"], flow_d_at=str(now.floor("s")),
                 d_flow=_f(v["flow"] - r["flow_p"]) if r.get("flow_p") is not None else None)
        for k, p in enumerate(v["pf"], 1):
            r[f"pf{k}_d"] = p["v"]
        ch = True
    if r.get("fund7_d") is None and v["fund_def"]:
        r.update(fund7_d=v["fund7"], fund7_d_at=str(now.floor("s")),
                 d_fund7=_f(v["fund7"] - r["fund7_p"], 8) if r.get("fund7_p") is not None else None)
        ch = True
    if r.get("decision_d") is None and r.get("flow_d") is not None and r.get("fund7_d") is not None:
        r["decision_d"] = decision_text(v["wk"], int(r["side"] or 0))
        r["changed"] = r["decision_d"] != r["decision_p"]
        ch = True
        if r["changed"]:
            print(f"[provlog] ATTENZIONE: decisione del {r['date']} con i dati definitivi = {r['decision_d']} "
                  f"(provvisoria: {r['decision_p']})")
    return ch


def update(f: pd.DataFrame, d: dict, wcur: dict | None, data_dir: Path, now: pd.Timestamp | None = None) -> dict:
    """Registra la decisione della domenica (se è il primo giro utile) e completa le righe provvisorie. Ritorna il riepilogo."""
    now = pd.Timestamp.utcnow().tz_localize(None) if now is None else pd.Timestamp(now)
    path = Path(data_dir) / FILE
    f = f[f["close"].notna()]
    if not len(f):
        print("[provlog] dati vuoti: nessuna registrazione")
        return summary(_read(path))
    perp_src = d.get("perp", pd.DataFrame()).get("source")
    perp_src = perp_src.fillna("binance") if perp_src is not None else None   # righe senza etichetta: archivio storico
    fund_src = d.get("funding", pd.DataFrame()).get("source")
    df = _read(path)
    rows = df.to_dict("records")
    have = {r["date"] for r in rows}
    changed = False
    last = f.index[-1].normalize()
    day = decision_sunday(last)
    lag = (last - day).days
    if str(day.date()) not in have and lag <= 1 and day in f.index:
        v = values(f, perp_src, fund_src, day)
        side = side_at(((wcur or {}).get("history") or {}).get("trades", []), str(day.date()))
        r = new_row(v, day, side, now, late=lag > 0)
        _check_vs_weekly(r, wcur)
        rows.append(r)
        changed = True
        print(f"[provlog] decisione del {r['date']} registrata: {r['decision_p']} · flusso {r['flow_p']} "
              f"({'/'.join(str(r[f'pf{k}_src']) for k in (1, 2, 3))}) · funding 7g {r['fund7_p']} ({r['fund7_src']})"
              + (" · registrata in ritardo" if r["late"] else ""))
    elif str(day.date()) not in have and lag > 1:
        print(f"[provlog] decisione del {day.date()} non registrata: dati già a {lag} giorni dopo la domenica "
              "(i valori provvisori non sono più quelli della decisione)")
    for r in rows:
        if r.get("decision_d") is not None:
            continue
        t = pd.Timestamp(r["date"])
        if t not in f.index:
            continue
        if complete(r, values(f, perp_src, fund_src, t), now):
            changed = True
    out = pd.DataFrame(rows, columns=COLS)
    if changed:
        path.parent.mkdir(exist_ok=True)
        out.to_csv(path, index=False)
    return summary(out)


def _check_vs_weekly(r: dict, wcur: dict | None) -> None:
    """Controllo di coerenza con lo stato W3 calcolato nello stesso giro (solo log)."""
    if not wcur:
        return
    st, sd = wcur.get("status"), wcur.get("signal_date")
    exp = None
    if st == "segnale" and sd == r["date"]:
        exp = f"ingresso {wcur.get('side')}"
    elif st == "uscita" and wcur.get("exit_date") == r["date"]:
        exp = f"uscita {wcur.get('reason')}"
    if exp and exp != r["decision_p"]:
        print(f"[provlog] controllo: esito registrato {r['decision_p']} diverso dallo stato W3 ({exp})")


def summary(df: pd.DataFrame, n: int = 5) -> dict:
    rows = df.to_dict("records") if len(df) else []
    keep = ("date", "decision_p", "decision_d", "changed", "flow_p", "flow_d", "d_flow", "fund7_p", "fund7_d", "d_fund7",
            "fund7_src", "pf1_src", "pf2_src", "pf3_src", "late")
    return {"rows": len(rows), "complete": sum(1 for r in rows if r.get("decision_d") is not None),
            "pending": sum(1 for r in rows if r.get("decision_d") is None),
            "changed": sum(1 for r in rows if r.get("changed") in (True, "True")),
            "last": [{k: r.get(k) for k in keep} for r in rows[-n:]]}
