"""tradera_test · stato di oggi del rilevatore su BTC, ETH, LMT, NVDA (ultime candele chiuse). Output: oggi.txt.
Azioni a prezzi non rettificati (come i grafici del trader)."""
from __future__ import annotations

import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import confronto as K  # noqa: E402
import tt_bt as B  # noqa: E402
import tt_detect as T  # noqa: E402

OUT = []
for a in ("BTC", "ETH", "LMT", "NVDA"):
    d = K.dati(a)
    r = T.detect(d)
    ix, C = d.index, d["close"].to_numpy(float)
    last = ix[-1].date()
    OUT.append(f"\n[{a}] ultima chiusura {last}: {C[-1]:.2f} · EMA50 {r['ema'][50][-1]:.2f} · EMA200 {r['ema'][200][-1]:.2f} · ATR {r['atr'][-1]:.2f}")
    for x in [x for x in r["signals"] + r["flips"] if len(d) - 1 - x["t"] <= 60]:
        kind = "ritest" if x in r["signals"] else "speculare"
        res = B.run_trade(*(d[k].to_numpy(float) for k in ("open", "high", "low", "close")), x["t"] + 1, x["side"], x["stop"],
                          x["tgt"], len(d) - 1) if x["t"] + 1 < len(d) else None
        st = ("non eseguito" if res is None else f"{res[2]} il {ix[res[0]].date()} a {res[1]:.2f}" if res[2] != "fine periodo"
              else f"APERTO (ultima {C[-1]:.2f})")
        OUT.append(f"  segnale {kind} {ix[x['t']].date()} {'long' if x['side'] > 0 else 'short'}: linea {x['lv']:.2f}, "
                   f"stop {x['stop']:.2f}, obiettivo {x['tgt']:.2f}, R:R {x.get('rr', float('nan')):.2f}, confluenza "
                   f"{x.get('conf', '-')}, filtro R:R≥2 {'sì' if x.get('rr', 0) >= T.P['RRMIN'] else 'no'} → {st}")
    for q in r["pending"]:
        OUT.append(f"  {q['kind']} lato {'long' if q['side'] > 0 else 'short'}: linea {ix[q['iA']].date()} {q['pA']:.2f} → "
                   f"{ix[q['iB']].date()} {q['pB']:.2f}, valore domani {q['lv_next']:.2f}"
                   + (f", stop {q['stop']:.2f}, obiettivo {q['tgt']:.2f}" if "stop" in q else ""))
    z = [x for x in T.zones(d) if 0.75 * C[-1] <= x["hi"] and x["lo"] <= 1.25 * C[-1]]
    OUT.append("  zone entro ±25%: " + "; ".join(f"{x['lo']:.2f}–{x['hi']:.2f} ({x['n']})" for x in z))
print("\n".join(OUT))
(HERE / "oggi.txt").write_text("\n".join(OUT).lstrip() + "\n")
