"""Laboratorio della dashboard: v2 (in uso) a confronto con i candidati della ricerca, su 10.000 $.

`build()` ricalcola v2 dal report di live.evaluate (trade e curva 10.000 $ a 1x e 2x, tetto di esposizione 5x)
e aggiunge i candidati elencati in research/lab_candidates.json. Per aggiungere un candidato basta un CSV dei trade
(colonne ingresso,lato,prezzo_ingresso,uscita,prezzo_uscita,motivo,movimento_%,pnl_capitale_%) e una voce nel JSON:
nessuna modifica al codice. Le metriche scritte nel JSON (quelle della ricerca) hanno la precedenza su quelle
ricalcolate dal CSV.
"""
from __future__ import annotations

import csv
import json
from pathlib import Path

import numpy as np
import pandas as pd

from .data import DATA_DIR

ROOT = Path(__file__).resolve().parent.parent
CANDIDATES = ROOT / "research" / "lab_candidates.json"
OUT = DATA_DIR / "lab.json"
CAP = 10000.0
KEYS = ("ingresso", "lato", "prezzo_ingresso", "uscita", "prezzo_uscita", "motivo", "movimento_pct", "pnl_capitale_pct")


def _curve(trades: list[dict], m: float, start: str, caps: list[float] | None = None) -> list[list]:
    """Curva 10.000 $ a gradini sulle date di uscita: pnl sul capitale × m, composto (× tetto per trade se dato)."""
    e, out = CAP, [[start, CAP]]
    for t, k in zip(trades, caps or [m] * len(trades)):
        e *= 1 + k * t["pnl_capitale_pct"] / 100
        if out[-1][0] == t["uscita"]:
            out[-1][1] = round(e, 2)
        else:
            out.append([t["uscita"], round(e, 2)])
    return out


def _metrics(trades: list[dict], c1: list, c2: list, start: str, end: str) -> dict:
    pn = np.array([t["pnl_capitale_pct"] for t in trades]) if trades else np.zeros(0)
    eq = np.array([v for _, v in c1])
    years = max((pd.Timestamp(end) - pd.Timestamp(start)).days / 365.25, 0.01)
    return {"trades_per_year": round(len(trades) / years, 1),
            "win_rate": round(float((pn > 0).mean() * 100), 1) if len(pn) else None,
            "avg_trade_pct": round(float(pn.mean()), 2) if len(pn) else 0.0,
            "total_return_pct": round((c1[-1][1] / CAP - 1) * 100, 1),
            "max_dd_pct": round(float((eq / np.maximum.accumulate(eq) - 1).min()) * 100, 1),
            "final_10k_1x": round(c1[-1][1]), "final_10k_2x": round(c2[-1][1])}


def v2_candidate(report: dict) -> dict:
    """v2 dallo storico di live.evaluate (dal 2022-03): trade chiusi, curve 1x e 2x con il tetto 5x come dal vivo."""
    from .live import BACKTEST_START
    closed = [t for t in report["trades"]["futures"] if t["exit"] != "open"]
    trades = [{"ingresso": (t.get("entry_time") or t["signal_date"])[:10], "lato": t["side"],
               "prezzo_ingresso": round(float(t["avg_entry"]), 1), "uscita": t["exit_date"],
               "prezzo_uscita": round(float(t["exit_px"]), 1) if t.get("exit_px") is not None else None,
               "motivo": t["exit"], "movimento_pct": t["pnl_pct_invested"], "pnl_capitale_pct": t["pnl_pct_capital"]}
              for t in closed]
    cap2 = [min(2.0, 5.0 / t["N"]) if t.get("N") else 2.0 for t in closed]
    c1, c2 = _curve(trades, 1, BACKTEST_START), _curve(trades, 2, BACKTEST_START, cap2)
    m = _metrics(trades, c1, c2, BACKTEST_START, report["date"])
    S = report.get("stats", {})
    m["trades_per_year"] = S.get("trades_per_year", m["trades_per_year"])
    dd = S.get("periods", {}).get("Totale", {}).get("max_dd_%")
    if dd is not None:
        m["max_dd_pct"] = dd   # DD sull'equity giornaliera, come in Statistiche
    return {"name": "v2 (in uso)", "status": "in uso",
            "rules": ["Setup giornalieri di flusso confermati da una chiusura 4h oltre il massimo (o minimo) recente.",
                      "Ingresso 40% alla conferma e 60% con limit a −0,5 ATR; stop 1 ATR, target unico +1R, massimo 14 giorni.",
                      "Size dal rischio sul capitale (più grande con flusso taker forte), leva massima 5x."],
            "metrics": m, "trades": trades, "curve_1x": c1, "curve_2x": c2}


def _num(x: str):
    try:
        return float(x)
    except (TypeError, ValueError):
        return x


def csv_candidate(c: dict) -> dict:
    """Candidato della ricerca da CSV dei trade (curva 1x a gradini sulle uscite, 2x = pnl × 2 composto)."""
    with open(ROOT / c["csv"], newline="") as fh:
        rows = list(csv.DictReader(fh))
    trades = [{k.replace("_%", "_pct"): (_num(v) if k not in ("ingresso", "uscita", "lato", "motivo") else v)
               for k, v in r.items() if k.replace("_%", "_pct") in KEYS} for r in rows]
    start = trades[0]["ingresso"] if trades else c.get("start", "2021-01-01")
    c1, c2 = _curve(trades, 1, start), _curve(trades, 2, start)
    if rows and "capitale_10k_1x" in rows[0]:   # capitale 1x della ricerca, se c'è (il pnl del CSV è arrotondato)
        c1 = [[start, CAP]]
        for t, r in zip(trades, rows):
            v = round(float(r["capitale_10k_1x"]), 2)
            if c1[-1][0] == t["uscita"]:
                c1[-1][1] = v
            else:
                c1.append([t["uscita"], v])
    m = _metrics(trades, c1, c2, start, c.get("end") or str(pd.Timestamp.now("UTC").date()))
    m.update(c.get("metrics") or {})
    return {"name": c["name"], "status": c.get("status", "su carta"), "rules": c.get("rules", []),
            "metrics": m, "trades": trades, "curve_1x": c1, "curve_2x": c2}


def build(report: dict | None = None, out: Path | None = OUT) -> dict:
    """Ricalcola il Laboratorio e lo salva in data/lab.json (out=None: non salva)."""
    if report is None:
        from .data import load_all
        from .features import build_features
        from .live import evaluate
        report = evaluate(build_features(load_all()))
    cands = [v2_candidate(report)]
    spec = json.loads(CANDIDATES.read_text()) if CANDIDATES.exists() else {"candidates": []}
    for c in spec.get("candidates", []):
        try:
            cands.append(csv_candidate(c))
        except Exception as e:  # noqa: BLE001   un candidato rotto non deve togliere gli altri
            print(f"[radar] laboratorio: candidato {c.get('name')!r} saltato: {e!r}")
    lab = {"updated": report["date"], "candidates": cands}
    if out is not None:
        out.write_text(json.dumps(lab, ensure_ascii=False, separators=(",", ":")))
    return lab
