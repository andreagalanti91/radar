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
    if ct["expectancy_%"] < bt["expectancy_%"]:
        why.append(f"aspettativa test peggiore ({ct['expectancy_%']} vs {bt['expectancy_%']})")
    if cand["train"]["expectancy_%"] < 0.8 * base["train"]["expectancy_%"]:
        why.append("peggiora troppo nel training: miglioramento probabilmente casuale")
    if ct["win_rate"] < bt["win_rate"] - 2:
        why.append(f"win rate test più basso ({ct['win_rate']} vs {bt['win_rate']})")
    if cf["max_dd_%"] < bf["max_dd_%"] - 3:
        why.append(f"drawdown peggiore ({cf['max_dd_%']} vs {bf['max_dd_%']})")
    if cf["total_return_%"] < bf["total_return_%"] * 1.05:
        why.append("miglioramento del rendimento totale sotto il 5%")
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


def main() -> None:
    f = build_features(load_all())
    base_p = Params()
    base = scorecard(f, base_p)
    if len(sys.argv) < 2:
        print(json.dumps(base, indent=1, default=str))
        return
    cand_p = replace(base_p, **json.loads(sys.argv[1]))
    cand = scorecard(f, cand_p)
    ok, why = promotion_gate(base, cand, robustness(f, cand_p))
    print(json.dumps({"base": base, "candidate": cand, "promote": ok, "reasons": why}, indent=1, default=str))


if __name__ == "__main__":
    main()
