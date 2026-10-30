"""Valutazione e criteri di promozione per il ciclo di miglioramento.

Una modifica alla strategia va live solo se supera TUTTI i controlli del gate:
evita che l'ottimizzazione continua adatti il modello al rumore del passato.

Uso:
  python -m radar.research                 scorecard della strategia attuale
  python -m radar.research '{"stop_atr": 3.5}'   confronta una variante dei parametri
"""
from __future__ import annotations

import json
import sys
import warnings
from dataclasses import replace

import numpy as np
import pandas as pd

from .backtest import run, summary
from .data import load_all
from .features import build_features
from .strategy import Params

warnings.filterwarnings("ignore")

TRAIN = ("2022-03-01", "2024-01-01")
TEST = ("2024-01-01", "2026-01-01")
HOLDOUT = ("2026-01-01", None)  # periodo di conferma: il candidato non deve peggiorarlo
NEIGHBORS = {  # perturbazioni per il test di robustezza
    "stop_atr": 0.5, "entry_step_atr": 0.25, "trail_atr": 1.0, "flow_threshold": 0.25, "max_hold": 15,
}


def _period(t: pd.DataFrame, a: str, b: str | None) -> pd.DataFrame:
    d = t["signal_date"].astype(str)
    return t[(d >= a) & (d < b)] if b else t[d >= a]


def mar(sm: dict) -> float:
    """Obiettivo: rendimento corretto per il rischio = rendimento totale / |max drawdown| (drawdown minimo 1%)."""
    return round(sm.get("total_return_%", 0) / max(1.0, abs(sm.get("max_dd_%", 0))), 2)


def path_from_events(tr: dict, close: pd.Series) -> list[tuple[str, float]]:
    """Ricostruisce il PnL giornaliero mark-to-market di un trade dai suoi eventi (entry/exit) e dalle chiusure.

    Unità: frazione del capitale a 1x (i pesi delle tranche sono quote del capitale). Approssimato: ignora
    commissioni e funding e usa prezzi/percentuali arrotondati degli eventi. Serve per i trade che non hanno
    il percorso esatto `mtm` registrato dal backtest (per esempio dallo stato live).
    """
    sg = 1 if tr["side"] == "long" else -1
    ev = [e for e in tr.get("events", []) if e.get("type") in ("entry", "exit")]
    if not ev:
        return []
    d0 = ev[0]["date"]
    d1 = str(tr["exit_date"]) if tr.get("exit_date") not in (None, "") and str(tr.get("exit_date")) != "NaT" else str(close.index[-1].date())
    days = close[(close.index >= pd.Timestamp(d0)) & (close.index <= pd.Timestamp(d1))]
    units = cost = pos = realized = 0.0
    out = []
    for day, px_close in days.items():
        ds = str(day.date())
        for e in ev:
            if e["date"] != ds:
                continue
            if e["type"] == "entry":
                q = e["pct"] / 100 / e["price"]
                units += q; pos += q; cost += q * e["price"]
            elif units > 0:
                avg = cost / units
                q = min(pos, e["pct"] / 100 * units)
                realized += sg * q * (e["price"] - avg)
                pos -= q
        if units > 0:
            avg = cost / units
            out.append((ds, float(realized + sg * pos * (px_close - avg))))
    return out


def daily_equity(t: pd.DataFrame, close: pd.Series | None = None, leverage: float = 1.0,
                 start: str | None = None) -> pd.Series:
    """Equity giornaliera mark-to-market (base 1.0) scalata per leva.

    Ogni giorno: equity = capitale realizzato all'apertura del trade x (1 + leva x PnL del trade a quel giorno),
    dove il PnL del trade include le uscite parziali già realizzate e il non realizzato della quantità residua
    alla chiusura del giorno (prezzo medio effettivo delle tranche riempite). Fra un trade e l'altro l'equity è
    piatta. Il giorno di uscita vale il risultato finale, quindi l'equity finale coincide con quella trade per trade.
    Usa il percorso esatto `mtm` del backtest se presente, altrimenti lo ricostruisce dagli eventi (serve `close`).
    """
    if t is None or t.empty:
        return pd.Series(dtype=float)
    rows: dict[str, float] = {}
    eq = 1.0
    t = t.sort_values("signal_date")
    if start is None:
        start = str(t["signal_date"].iloc[0])
    rows[str(pd.Timestamp(start).date())] = 1.0
    for _, tr in t.iterrows():
        path = tr.get("mtm") if "mtm" in t and isinstance(tr.get("mtm"), list) else None
        if path is None:
            if close is None:
                raise ValueError("serve la serie delle chiusure per ricostruire il percorso dagli eventi")
            path = path_from_events(tr.to_dict(), close)
        for ds, v in path:
            rows[ds] = eq * (1 + leverage * v)
        if path and tr["exit"] != "open":
            eq = eq * (1 + leverage * path[-1][1])
    s = pd.Series(rows)
    s.index = pd.to_datetime(s.index)
    s = s.sort_index()
    full = pd.date_range(s.index[0], s.index[-1], freq="D")
    return s.reindex(full).ffill()


def drawdown_stats(eq: pd.Series, t: pd.DataFrame | None = None) -> dict:
    """Max drawdown dell'equity giornaliera, data del minimo, durata (picco→minimo, picco→recupero) e trade responsabile."""
    if eq is None or eq.empty:
        return {"max_dd_%": 0.0}
    peak = eq.cummax()
    dd = eq / peak - 1
    trough = dd.idxmin()
    pk = eq.loc[:trough].idxmax()
    after = eq.loc[trough:]
    rec = after[after >= eq.loc[pk]]
    out = {
        "max_dd_%": round(float(dd.min()) * 100, 1),
        "peak": str(pk.date()), "trough": str(trough.date()),
        "recovery": str(rec.index[0].date()) if len(rec) else None,
        "days_peak_to_trough": int((trough - pk).days),
        "days_underwater": int(((rec.index[0] if len(rec) else eq.index[-1]) - pk).days),
        "return_%": round(float(eq.iloc[-1] - 1) * 100, 1),
    }
    if t is not None and not t.empty:
        sd = pd.to_datetime(t["signal_date"].astype(str))
        ed = pd.to_datetime(t["exit_date"].astype(str), errors="coerce").fillna(eq.index[-1])
        hit = t[(sd < trough) & (ed >= trough)]
        if len(hit):
            out["trade"] = f"{hit.iloc[0]['signal_date']} {hit.iloc[0]['side']} {hit.iloc[0]['setup']} ({hit.iloc[0]['exit']})"
        # trade aperti fra il picco e il minimo (chi ha prodotto il drawdown)
        inside = t[(ed > pk) & (sd < trough)]
        out["trades_in_dd"] = [f"{r['signal_date']} {r['setup']} {r['exit']} {r['pnl_pct_capital']:+.2f}%" for _, r in inside.iterrows()]
    return out


def dd_daily(t: pd.DataFrame, close: pd.Series | None = None, levels=(1, 2, 3)) -> dict:
    """Drawdown reale (mark-to-market giornaliero) a più leve, con rendimento/drawdown corrispondente."""
    out = {}
    for L in levels:
        st = drawdown_stats(daily_equity(t, close, L), t)
        st["mar"] = round(st.get("return_%", 0) / max(1.0, abs(st["max_dd_%"])), 2)
        out[f"{L}x"] = st
    return out


def windows(t: pd.DataFrame) -> dict:
    """Aspettativa per semestre (validazione su finestre consecutive)."""
    if t.empty:
        return {}
    t = t[t["exit"] != "open"]
    d = pd.to_datetime(t["signal_date"].astype(str))
    key = d.dt.year.astype(str) + "H" + np.where(d.dt.month <= 6, "1", "2")
    return {k: round(float(g.mean()), 3) for k, g in t["pnl_pct_capital"].groupby(key.values)}


def scorecard(f: pd.DataFrame, p: Params, signals=None) -> dict:
    t = run(f, p, "futures", TRAIN[0], signals=signals)
    sp = run(f, p, "spot", TRAIN[0], signals=signals)
    return {
        "train": summary(_period(t, *TRAIN)),
        "test": summary(_period(t, *TEST)),
        "holdout": summary(_period(t, *HOLDOUT)),
        "full": summary(t),
        "full_2x": summary(t, 2),
        "spot_full": summary(sp),
        # pnl per trade (chiave: data del segnale) per misurare quanto il miglioramento è concentrato
        "mar": mar(summary(t)),
        # drawdown reale: equity giornaliera mark-to-market (posizione aperta valutata alla chiusura), 1x/2x/3x
        "dd_daily": dd_daily(t, f["close"]),
        "windows": windows(t),
        "pnls": [float(x) for x in t[t["exit"] != "open"]["pnl_pct_capital"]] if len(t) else [],
        "pnl_by_signal": {str(d): float(v) for d, v in zip(t["signal_date"], t["pnl_pct_capital"])} if len(t) else {},
    }


def robustness(f: pd.DataFrame, p: Params) -> list[dict]:
    out = []
    for k, step in NEIGHBORS.items():
        for sgn in (-1, 1):
            v = getattr(p, k) + sgn * step
            if v <= 0:
                continue
            q = replace(p, **{k: type(getattr(p, k))(v)})
            s = summary(run(f, q, "futures", TRAIN[0]))
            out.append({"param": k, "value": v, "trades": s["trades"], "win_rate": s.get("win_rate", 0),
                        "total_return_%": s.get("total_return_%", 0)})
    return out


def promotion_gate(base: dict, cand: dict, cand_robust: list[dict]) -> tuple[bool, list[str]]:
    """Ritorna (promuovibile, motivi). Il candidato deve migliorare senza peggiorare il rischio."""
    why = []
    bt, ct = base["test"], cand["test"]
    bf, cf = base["full"], cand["full"]
    if ct["trades"] < 0.8 * bt["trades"]:
        why.append(f"troppi pochi trade nel test ({ct['trades']} vs {bt['trades']})")
    # obiettivo principale: rendimento corretto per il rischio
    if cand.get("mar", 0) < base.get("mar", 0) * 1.05:
        why.append(f"rendimento/drawdown non migliora almeno del 5% ({cand.get('mar')} vs {base.get('mar')})")
    if ct["expectancy_%"] < bt["expectancy_%"] - 0.1:
        why.append(f"aspettativa test peggiore ({ct['expectancy_%']} vs {bt['expectancy_%']})")
    if cand["train"]["expectancy_%"] < 0.8 * base["train"]["expectancy_%"]:
        why.append("peggiora troppo nel training: miglioramento probabilmente casuale")
    if ct["win_rate"] < bt["win_rate"] - 2:
        why.append(f"win rate test più basso ({ct['win_rate']} vs {bt['win_rate']})")
    # drawdown: misurato sull'equity giornaliera mark-to-market (reale) se disponibile, altrimenti trade per trade
    bdd = base.get("dd_daily", {}).get("1x", {}).get("max_dd_%", bf["max_dd_%"])
    cdd = cand.get("dd_daily", {}).get("1x", {}).get("max_dd_%", cf["max_dd_%"])
    if cdd < bdd - 3:
        why.append(f"drawdown giornaliero peggiore ({cdd} vs {bdd})")
    if cf.get("win_rate_clean", 0) < bf.get("win_rate_clean", 0) - 3:
        why.append(f"win rate pulito più basso ({cf.get('win_rate_clean')} vs {bf.get('win_rate_clean')})")
    # validazione su finestre semestrali: deve reggere nella maggior parte dei periodi
    bw, cw = base.get("windows", {}), cand.get("windows", {})
    common = [k for k in bw if k in cw]
    if common:
        better = sum(cw[k] >= bw[k] for k in common) / len(common)
        worst = min(cw[k] - bw[k] for k in common)
        if better < 0.6:
            why.append(f"migliore solo nel {better*100:.0f}% dei semestri")
        if worst < -1.5:
            why.append(f"un semestre peggiora di {worst:.2f} punti per trade")
    # test statistico: probabilità che l'aspettativa del candidato superi la base (ricampionamento)
    bp_, cp_ = np.array(base.get("pnls", [])), np.array(cand.get("pnls", []))
    if len(bp_) and len(cp_):
        rng = np.random.default_rng(7)
        pb = rng.choice(bp_, (2000, len(bp_))).mean(1)
        pc = rng.choice(cp_, (2000, len(cp_))).mean(1)
        prob = float((pc > pb).mean())
        if prob < 0.75:
            why.append(f"miglioramento non significativo (probabilità {prob*100:.0f}% < 75%)")
    bh, ch = base["holdout"], cand["holdout"]
    if bh.get("trades") and ch.get("expectancy_%", 0) < bh.get("expectancy_%", 0) - 0.25:
        why.append(f"peggiora nel periodo di conferma 2026 ({ch.get('expectancy_%')} vs {bh.get('expectancy_%')})")
    # concentrazione: il miglioramento non deve dipendere da uno o due trade
    bp, cp = base.get("pnl_by_signal", {}), cand.get("pnl_by_signal", {})
    diffs = sorted((cp.get(k, 0.0) - bp.get(k, 0.0) for k in set(bp) | set(cp)), reverse=True)
    gain = sum(diffs)
    if gain > 0 and diffs and (gain - diffs[0]) <= 0:
        why.append(f"miglioramento concentrato: senza il trade che migliora di più il guadagno netto è {gain - diffs[0]:+.2f} punti")
    elif gain > 0 and len(diffs) > 1 and (gain - diffs[0] - diffs[1]) <= 0:
        why.append("miglioramento concentrato: dipende dai due trade che migliorano di più")
    bad = [r for r in cand_robust if r["total_return_%"] <= 0 or r["win_rate"] < 70]
    if bad:
        why.append(f"non robusto: {len(bad)} varianti vicine in perdita o con win rate < 70%")
    return (not why), why


def cross_asset(p: Params, symbol: str = "SOLUSDT") -> dict:
    """Banco di prova su un altro asset (dati già in cache in data/<SYMBOL>/): non operativo."""
    from . import data as D
    old = D.DATA_DIR
    try:
        D.DATA_DIR = old / symbol
        d = load_all()
    finally:
        D.DATA_DIR = old
    t = run(build_features(d), p, "futures", TRAIN[0])
    return {**summary(t), "mar": mar(summary(t))}


def main() -> None:
    f = build_features(load_all())
    base_p = Params()
    base = scorecard(f, base_p)
    if len(sys.argv) < 2:
        base.pop("pnls", None); base.pop("pnl_by_signal", None)
        print(json.dumps(base, indent=1, default=str))
        return
    cand_p = replace(base_p, **json.loads(sys.argv[1]))
    cand = scorecard(f, cand_p)
    ok, why = promotion_gate(base, cand, robustness(f, cand_p))
    xb, xc = cross_asset(base_p), cross_asset(cand_p)
    if xc.get("expectancy_%", 0) < xb.get("expectancy_%", 0) - 0.5:
        ok = False
        why.append(f"peggiora su SOL (banco di prova): {xc.get('expectancy_%')} vs {xb.get('expectancy_%')}")
    for d in (base, cand):
        d.pop("pnls", None); d.pop("pnl_by_signal", None)
    print(json.dumps({"base": base, "candidate": cand, "sol_base": xb, "sol_candidate": xc, "promote": ok, "reasons": why}, indent=1, default=str))


if __name__ == "__main__":
    main()
