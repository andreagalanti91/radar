"""Rapporto ufficiale W3.2 (BTC) · convenzione unica del 25/11/2026 (stato/STATO-rapporto-w32.md).

- Motore: radar.weekly.simulate INVARIATO (nessuna modifica a radar/). 10.000 $, 1x, commissioni, slippage e funding del motore.
- Dati: frame del tool = radar.features.build_features(data/) (dal 01/09/2019). Per i periodi che iniziano prima del 2021 il frame
  del tool è preceduto dalla storia lunga della ricerca (research/p2_nuovi/data/f_long.csv.gz: prezzi identici a data/, pf14z
  stimato dal CVD spot solo fino all'11/04/2020), come in research/v1_confronto/s2_w32.py.
  Regola: data/ da solo dove basta (periodi dal 2021: identico al tool), storia lunga solo dove data/ non arriva.
- Ogni periodo parte da FLAT il primo giorno indicato; la posizione aperta alla fine è valutata all'ultima chiusura (equity del
  motore, come il tool) e contata a parte dalle operazioni chiuse.
- Data di fine: ultimo giorno chiuso dei dati del repo (data/ del ramo pubblicato, aggiornamento del 25/11/2026 → 24/11/2026).

Uso:
  python research/w32_ufficiale/w32_ufficiale.py freeze [DATA_DIR]   # congela i frame (predefinito: data/ del repo)
  python research/w32_ufficiale/w32_ufficiale.py                     # calcola tabelle e CSV dai frame congelati
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT))
from radar import weekly as W  # noqa: E402

COLS = ["open", "high", "low", "close", "pf14z", "funding", "atr"]
F_TOOL, F_LONG = HERE / "f_tool.csv.gz", HERE / "f_lungo.csv.gz"
CAP = 10000.0


def freeze(data_dir: str | None = None) -> None:
    import radar.data as D
    from radar.features import build_features
    sys.path.insert(0, str(ROOT / "research" / "p2_nuovi"))
    from p2_data import load
    if data_dir:
        D.DATA_DIR = Path(data_dir)
    fv = build_features(D.load_all())
    fv = fv[fv["close"].notna()]
    fl = load()["fl"]
    c = fl.index.intersection(fv.index)
    for k in ("open", "high", "low", "close"):
        assert (fl.loc[c, k] - fv.loc[c, k]).abs().max() == 0, k
    both = fv["pf14z"].reindex(c).notna()
    assert (fl.loc[c[both], "pf14z"] - fv.loc[c[both], "pf14z"]).abs().max() < 1e-9
    f = pd.concat([fl, fv[fv.index > fl.index[-1]]]).sort_index()
    assert f.loc["2019-09-01":"2020-04-11", "pf14z"].notna().all()   # nessun buco di flusso alla giunzione (lezione 126)
    fv[[k for k in COLS if k in fv]].to_csv(F_TOOL)
    f[[k for k in COLS if k in f]].to_csv(F_LONG)
    print("frame tool", fv.index[0].date(), "→", fv.index[-1].date(), "| frame lungo", f.index[0].date(), "→", f.index[-1].date())


def rd(p: Path) -> pd.DataFrame:
    return pd.read_csv(p, index_col=0, parse_dates=True)


def frame_for(start: str, ft: pd.DataFrame, fl: pd.DataFrame) -> pd.DataFrame:
    return ft if pd.Timestamp(start) >= pd.Timestamp("2021-01-01") else fl


def run(start: str, end: str | None, ft, fl) -> dict:
    f = frame_for(start, ft, fl)
    if end:
        f = f[f.index <= end]
    return W.simulate(f, start=start, capital=CAP)


def bh(f: pd.DataFrame, start: str, end: str | None) -> pd.Series:
    """BTC comprato all'apertura del primo giorno (commissione spot + slittamento del motore), valutato alla chiusura."""
    f = f.loc[start:end]
    px0 = f["open"].iloc[0] * (1 + W.SLIP)
    return CAP * (1 - W.FEE_SPOT) * f["close"] / px0


def stats(eq: pd.Series) -> dict:
    e = eq / CAP
    yrs = (e.index[-1] - e.index[0] + pd.Timedelta(days=1)).days / 365.25
    dr = e.pct_change().fillna(e.iloc[0] - 1)
    dd = float((e / e.cummax().clip(lower=1.0) - 1).min())
    cagr = float(e.iloc[-1]) ** (1 / yrs) - 1
    return {"finale": round(float(eq.iloc[-1])), "rend_tot": 100 * (float(e.iloc[-1]) - 1), "cagr": 100 * cagr,
            "dd": 100 * dd, "sharpe": float(dr.mean() / dr.std() * np.sqrt(365)) if dr.std() > 0 else np.nan,
            "cagr_dd": cagr / abs(dd) if dd < 0 else np.nan, "anni": yrs}


def trade_stats(r: dict, eq: pd.Series) -> dict:
    tr = r["trades"]
    pn = np.array([t["pnl"] for t in tr])
    w, l = pn[pn > 0], pn[pn <= 0]
    streak = best_streak = 0
    for p in pn:
        streak = streak + 1 if p <= 0 else 0
        best_streak = max(best_streak, streak)
    dur = [(pd.Timestamp(t["exit"]) - pd.Timestamp(t["entry"])).days for t in tr]
    held = pd.Series(False, index=eq.index)
    for t in tr:
        held.loc[t["entry"]:(pd.Timestamp(t["exit"]) - pd.Timedelta(days=1))] = True
    if r["open"]:
        held.loc[r["open"]["entry"]:] = True
    side = lambda s: [t["pnl"] for t in tr if t["side"] == s]  # noqa: E731
    wr = lambda x: (f"{100 * np.mean(np.array(x) > 0):.0f}% ({sum(np.array(x) > 0)}/{len(x)})" if x else "–")  # noqa: E731
    o = r["open"]
    return {"chiuse": len(tr), "aperta": (f"{o['side']} dal {o['entry']} {100 * o['pnl']:+.1f}%" if o else "nessuna"),
            "win_rate": 100 * len(w) / len(pn) if len(pn) else np.nan, "vinte": int(len(w)),
            "profit_factor": (w.sum() / -l.sum()) if l.sum() < 0 else np.inf,
            "guadagno_medio": 100 * w.mean() if len(w) else np.nan, "perdita_media": 100 * l.mean() if len(l) else np.nan,
            "migliore": 100 * pn.max() if len(pn) else np.nan, "peggiore": 100 * pn.min() if len(pn) else np.nan,
            "perdite_di_fila": best_streak, "durata_media_gg": float(np.mean(dur)) if dur else np.nan,
            "tempo_in_posizione": 100 * float(held.mean()), "wr_long": wr(side("long")), "wr_short": wr(side("short"))}


def tlist(r: dict) -> pd.DataFrame:
    rows = []
    for t in r["trades"] + ([dict(r["open"], exit=None, exit_px=None, reason="open")] if r["open"] else []):
        rows.append({"verso": t["side"], "segnale": t["signal"], "entrata": t["entry"], "uscita": t["exit"] or "aperta",
                     "prezzo_in": t["entry_px"], "prezzo_out": t["exit_px"] if t["exit_px"] else round(t["last"], 2),
                     "esposizione": t["expo"], "mercato": t["market"], "sul_capitale_pct": round(100 * t["pnl"], 2),
                     "motivo": W.REASONS.get(t["reason"], t["reason"])})
    return pd.DataFrame(rows)


def fmt(x, d=1, pct=False, sign=False):
    if isinstance(x, str):
        return x
    if x is None or (isinstance(x, float) and np.isnan(x)):
        return "–"
    if np.isinf(x):
        return "∞"
    s = f"{x:+,.{d}f}" if sign else f"{x:,.{d}f}"
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return s + ("%" if pct else "")


def main() -> None:
    ft, fl = rd(F_TOOL), rd(F_LONG)
    END = str(ft.index[-1].date())
    assert fl.index[-1] == ft.index[-1]
    out = [f"Data di fine: {END} (ultimo giorno chiuso). Frame tool dal {ft.index[0].date()}, frame lungo dal {fl.index[0].date()}."]
    y12 = str((ft.index[-1] - pd.DateOffset(years=1) + pd.Timedelta(days=1)).date())
    periods = [("Dal 01/01/2018", "2018-01-01", None), ("Dal 01/01/2021 (tool)", "2021-01-01", None),
               ("2018–2020", "2018-01-01", "2020-12-31"), ("2021–2023", "2021-01-01", "2023-12-31"),
               ("2024–oggi", "2024-01-01", None), (f"Ultimi 12 mesi (dal {y12})", y12, None)]
    rows, runs = [], {}
    for name, s, e in periods:
        r = run(s, e, ft, fl)
        runs[name] = r
        eq = r["equity"]
        b = bh(frame_for(s, ft, fl), s, e)
        rows.append({"periodo": name, "inizio": s, "fine": e or END, **stats(eq), **trade_stats(r, eq),
                     "bh_finale": round(float(b.iloc[-1])), "bh_rend": 100 * (float(b.iloc[-1]) / CAP - 1),
                     "bh_cagr": stats(b)["cagr"], "bh_dd": stats(b)["dd"], "bh_sharpe": stats(b)["sharpe"]})
    tp = pd.DataFrame(rows)
    tp.to_csv(HERE / "tab_periodi.csv", index=False, float_format="%.4f")
    out.append(tp.drop(columns=["inizio"]).T.to_string())

    # anno per anno sulla serie continua dal 2018 (e quella del tool dal 2021, che differisce solo nel 2021)
    r18, r21 = runs["Dal 01/01/2018"], runs["Dal 01/01/2021 (tool)"]
    e18, e21 = r18["equity"], r21["equity"]
    b18 = bh(fl, "2018-01-01", None)
    yr = []
    for y in range(2018, ft.index[-1].year + 1):
        def seg(e):
            prev = e[e.index.year < y]
            base = prev.iloc[-1] if len(prev) else CAP
            s = pd.concat([pd.Series([base]), e[e.index.year == y]])
            return 100 * (float(s.iloc[-1]) / base - 1), 100 * float((s / s.cummax() - 1).min())
        rr, dd = seg(e18)
        br, bd = seg(b18)
        nchi = sum(pd.Timestamp(t["exit"]).year == y for t in r18["trades"])
        nent = sum(pd.Timestamp(t["entry"]).year == y for t in r18["trades"] + ([r18["open"]] if r18["open"] else []))
        row = {"anno": y, "rend": rr, "dd": dd, "chiuse_nell_anno": nchi, "aperte_nell_anno": nent, "bh_rend": br, "bh_dd": bd}
        if y >= 2021:
            row["rend_tool_dal2021"], row["dd_tool_dal2021"] = seg(e21)
        yr.append(row)
    ty = pd.DataFrame(yr)
    ty.to_csv(HERE / "tab_anni.csv", index=False, float_format="%.2f")
    out.append(ty.to_string(float_format=lambda x: f"{x:.1f}"))

    t18, t21 = tlist(r18), tlist(r21)
    t18.to_csv(HERE / "tab_operazioni_2018.csv", index=False)
    t21.to_csv(HERE / "tab_operazioni_2021.csv", index=False)
    out.append(t18.to_string())
    pd.DataFrame({"w32_dal2018": e18, "bh_dal2018": b18}).to_csv(HERE / "equity_dal2018.csv", float_format="%.2f")
    pd.DataFrame({"w32_dal2021": e21, "bh_dal2021": bh(ft, "2021-01-01", None)}).to_csv(HERE / "equity_dal2021.csv", float_format="%.2f")

    # posizione aperta: livelli d'uscita (blocco descrittivo del tool) su 10.000 $
    ev = W.evaluate(ft, capital=CAP)
    u = ev.get("uscite") or {}
    out.append("POSIZIONE APERTA (evaluate, 10k): " + str({k: ev.get(k) for k in ("status", "side", "signal_date", "entry", "entry_px",
               "expo", "stop0", "trail", "best", "price", "move_pct", "pnl_pct", "ema21", "atr_w", "fund7", "flow")}))
    for k in ("trail", "ema21", "dist"):
        out.append(f"  uscita {k}: " + str(u.get(k)))
    h = ev["history"]
    out.append(f"TOOL evaluate: final_10k_1x {h['final_10k_1x']} | m1 {h['m1']}")
    assert abs(h["final_10k_1x"] - rows[1]["finale"]) <= 1, "il dal 2021 non coincide con il tool"

    # robustezza: senza le operazioni migliori (prodotto dei risultati chiusi + aperta a fine periodo), rischio 10% vs 25%
    rob = []
    for name in ("Dal 01/01/2018", "Dal 01/01/2021 (tool)"):
        r = runs[name]
        pn = sorted([t["pnl"] for t in r["trades"]] + ([r["open"]["pnl"]] if r["open"] else []), reverse=True)
        prod = lambda x: CAP * float(np.prod([1 + p for p in x]))  # noqa: E731
        rob.append({"periodo": name, "variante": "tutte (prodotto)", "finale": prod(pn)})
        rob.append({"periodo": name, "variante": "senza la migliore", "finale": prod(pn[1:])})
        rob.append({"periodo": name, "variante": "senza le 3 migliori", "finale": prod(pn[3:])})
    for risk in (0.10, 0.25, 0.30):
        W.R_LONG = W.R_SHORT = risk
        try:
            for name, s, e in periods[:3]:
                r = run(s, e, ft, fl)
                st, ts = stats(r["equity"]), trade_stats(r, r["equity"])
                rob.append({"periodo": name, "variante": f"rischio {int(risk * 100)}%", "finale": st["finale"], "dd": st["dd"],
                            "cagr": st["cagr"], "cagr_dd": st["cagr_dd"], "win_rate": ts["win_rate"], "chiuse": ts["chiuse"]})
        finally:
            W.R_LONG = W.R_SHORT = 0.25
    tr_ = pd.DataFrame(rob)
    tr_.to_csv(HERE / "tab_robustezza.csv", index=False, float_format="%.2f")
    out.append(tr_.to_string(float_format=lambda x: f"{x:,.1f}"))

    # controlli delle cifre circolate (stesso motore, convenzioni diverse)
    chk = {}
    chk["dal 2021 con frame lungo (riscaldamento indicatori dal 2014)"] = round(float(W.simulate(fl, start="2021-01-01")["equity"].iloc[-1]))
    chk["dal 2021 come tratto della serie continua dal 2018"] = round(CAP * float(e18.iloc[-1] / e18[e18.index < "2021-01-01"].iloc[-1]))
    for d in ("2026-11-15", "2026-11-21", "2026-11-22"):
        chk[f"dal 2021, dati fino al {d}"] = round(float(W.simulate(ft[ft.index <= d])["equity"].iloc[-1]))
        chk[f"dal 2018 continua, dati fino al {d}"] = round(float(W.simulate(fl[fl.index <= d], start="2018-01-01")["equity"].iloc[-1]))
    a = W.simulate(fl[fl.index <= "2020-12-31"], start="2018-01-01")
    chk["2018–2020 con la posizione chiusa d'ufficio al 31/12/2020 (commissione)"] = round(
        float(a["equity"].iloc[-1]) * (1 + a["open"]["pnl_close"]) / (1 + a["open"]["pnl"])) if a["open"] else None
    out.append("CONTROLLI: " + "\n  ".join(f"{k}: {v}" for k, v in chk.items()))
    pd.Series(chk).to_csv(HERE / "tab_controlli.csv", header=["finale"])
    (HERE / "risultati.txt").write_text("\n\n".join(out) + "\n", encoding="utf-8")
    print("\n\n".join(out))


if __name__ == "__main__":
    pd.set_option("display.width", 250)
    pd.set_option("display.max_columns", 40)
    if len(sys.argv) > 1 and sys.argv[1] == "freeze":
        freeze(sys.argv[2] if len(sys.argv) > 2 else None)
    else:
        main()
