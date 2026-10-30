"""Osservazione di altri asset (oggi SOL) con la strategia BTC, senza inserirli nel tool operativo.

Segue i segnali "su carta": stesso modello e stessi parametri di BTC, dati in una cache separata
(data/<SYMBOL>/), nessun alert operativo e nessuna voce in dashboard. Serve ad accumulare trade fuori
campione per decidere più avanti se l'asset merita di entrare.

Uso: python -m radar.observe SOLUSDT       stampa lo stato in JSON e aggiorna data/<SYMBOL>/observe.json
"""
from __future__ import annotations

import json
import sys
import warnings
from datetime import datetime, timezone

import pandas as pd

from . import data as D
from .backtest import run, summary
from .features import build_features
from .live import _clean
from .strategy import Params, compute_signals, explain
from .zones import latest_zone

warnings.filterwarnings("ignore")
OBS_START = "2026-10-30"  # inizio dell'osservazione fuori campione
BTC_DIR, BTC_SYMBOL, BTC_INST = D.DATA_DIR, D.SYMBOL, D.OKX_INST


def observe(symbol: str = "SOLUSDT") -> dict:
    base = symbol.replace("USDT", "")
    D.SYMBOL, D.OKX_INST, D.DATA_DIR = symbol, f"{base}-USDT-SWAP", BTC_DIR / symbol
    D.DATA_DIR.mkdir(parents=True, exist_ok=True)
    try:
        btc_fng = BTC_DIR / "fng.csv"  # il Fear & Greed è unico per il mercato
        d = D.update_all(verbose=False)
        d["fng"] = pd.read_csv(btc_fng, index_col=0, parse_dates=True)
        f = build_features(d)
    finally:
        D.SYMBOL, D.OKX_INST, D.DATA_DIR = BTC_SYMBOL, BTC_INST, BTC_DIR
    p = Params()
    s = compute_signals(f, p)
    s = s.loc[: s["score"].last_valid_index()]
    last = s.iloc[-1]
    t = run(f.loc[: s.index[-1]], p, "futures", "2022-03-01")
    t_obs = t[t["signal_date"].astype(str) >= OBS_START]
    opened = t[t["exit"] == "open"]
    side = "long" if last["long_sig"] else "short" if last["short_sig"] else None
    out = {
        "symbol": symbol, "date": str(last.name.date()), "price": float(last["close"]),
        "score": float(last["score"]), "signal": side and {"side": side, "setup": last["setup"],
                                                          "why": explain(last, last["setup"], p)},
        "open_trade": opened.drop(columns=["events", "plan", "mtm"], errors="ignore").to_dict("records")[0] if len(opened) else None,
        "zone": {k: v for k, v in latest_zone(f.loc[: s.index[-1]]).items() if k != "stats"},
        "observation": {"since": OBS_START, **summary(t_obs)},
        "backtest_full": summary(t),
        "updated": datetime.now(timezone.utc).isoformat(timespec="minutes"),
    }
    out = _clean(out)
    (BTC_DIR / symbol / "observe.json").write_text(json.dumps(out, indent=1, default=str))
    return out


if __name__ == "__main__":
    print(json.dumps(observe(sys.argv[1] if len(sys.argv) > 1 else "SOLUSDT"), indent=1, default=str))
