"""dimensione · FASE 1 · CONTEGGI senza rendimenti di varianti.
- buchi dei dati (OI, funding) e prima domenica in cui ogni condizione è calcolabile;
- quota di domeniche in cui ogni condizione è vera (descrittiva, per anno, senza esiti);
- per variante (e vicini), asset e periodo: quante operazioni di W3.2 sono toccate, per anno, con esposizione prima/dopo;
- controllo che la dimensione non cambi nessuna operazione (stesse date di segnale, entrata, uscita, motivo);
- caso finto dei criteri (lezione 101): "dimezzare tutto" su una serie sintetica.
Non stampa capitale, P&L o DD di nessuna variante. Uscita: conteggi_output.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import regole as R  # noqa: E402

LOG = []
PERIODI = [("BTC", "dal 2018", True, "2018-01-01"), ("BTC", "dal 2021", False, "2021-01-01"), ("ETH", "dal 2021", False, "2021-01-11")]


def p(*a):
    s = " ".join(str(x) for x in a); print(s); LOG.append(s)


def first_true_valid(flagthr):
    v = flagthr.dropna()
    return v.index[0].date() if len(v) else None


def buchi():
    p("=== DATI E BUCHI ===")
    for a, lg in (("BTC", True), ("ETH", False)):
        f = R.frame(a, lg)
        oi = R.oi_chg28(a)
        thr_oi = oi.shift(1).rolling(R.WIN, min_periods=R.MINOBS).quantile(0.9)
        fu = R.fund7(f)
        thr_fu = fu.shift(1).rolling(R.WIN, min_periods=R.MINOBS).quantile(0.9)
        p(f"{a}: OI Binance (data/{'metrics' if a == 'BTC' else 'eth_metrics'}.csv) primo valore {oi.first_valid_index().date()}, "
          f"soglia p90 calcolabile dal {first_true_valid(thr_oi)}; funding giornaliero dal {f['funding'].first_valid_index().date()}"
          f" (primo ≠ 0 {f['funding'][f['funding'].fillna(0) != 0].index[0].date()}), soglia p90 fund7 calcolabile dal "
          f"{first_true_valid(thr_fu)}; prezzo/SMA40 dal {R.weekly(f)['sma'].first_valid_index().date()}")
    p("→ D1 non può toccare nulla prima della soglia funding (BTC/ETH ~07/2020) e usa solo il funding fino alla soglia OI (~06/2022).")


def quote():
    p("\n=== QUOTA DI DOMENICHE CON LA CONDIZIONE VERA (descrittiva, tutte le domeniche, senza esiti) ===")
    for a, lg in (("BTC", True), ("ETH", False)):
        f = R.frame(a, lg); w = R.weekly(f)
        c1, oi, fu = R.affollato(f, a, 0.90)
        tab = pd.DataFrame({"D1 OI>p90": oi, "D1 fund7>p90 e >neutro": fu, "D1": c1, "D2 età≤3": R.giovane(f, 3),
                            "regime long": (w["close"] > w["sma"]), "D4 <−35%": R.short_tardo(f, 0.35)})
        tab = tab[tab.index >= "2018-01-01"]
        y = (100 * tab.groupby(tab.index.year).mean()).round(0).astype(int)
        p(f"{a} (% delle domeniche):\n" + y.to_string())


def sig_list(o):
    tr = o["trades"] + ([dict(o["open"], exit=None, reason="open")] if o["open"] else [])
    return [(t["signal"], t["entry"], t.get("exit"), t.get("reason"), t["side"]) for t in tr]


def conteggi():
    p("\n=== OPERAZIONI TOCCATE (W3.2 di base: stesse operazioni per costruzione) ===")
    rows = []
    for a, per, lg, st in PERIODI:
        f = R.frame(a, lg)
        base = R.sim(f, st)
        bl = sig_list(base)
        nl = sum(1 for x in bl if x[4] == "long"); ns = len(bl) - nl
        p(f"\n--- {a} {per}: W3.2 {len(bl)} operazioni ({nl} long, {ns} short; aperta inclusa)")
        for v in ("D1", "D2", "D3", "D4"):
            for par in [R.PAR[v]] + R.VICINI[v]:
                c = R.fattore(v, f, a, par)
                lato = R.LATO[v]
                hit = R.toccate(base, c, lato)
                o = R.sim(f, st, cond=c, lato=lato)
                same = sig_list(o) == bl                       # la dimensione non cambia le operazioni
                ex_new = {t["signal"]: t["expo"] for t in o["trades"] + ([o["open"]] if o["open"] else [])}
                yrs = {int(k): int(v) for k, v in pd.Series([pd.Timestamp(t["signal"]).year for t in hit], dtype=int).value_counts().sort_index().items()}
                tag = "scelta" if par == R.PAR[v] else "vicino"
                det = ", ".join(f"{t['signal']} {t['side'][0].upper()} {t['expo']:.2f}→{ex_new[t['signal']]:.2f}" for t in hit)
                p(f"{v} {str(par):11s} ({tag}): toccate {len(hit):2d}/{nl if lato > 0 else ns} "
                  f"{'long' if lato > 0 else 'short'} · per anno {yrs} · operazioni invariate: "
                  f"{'sì' if same else 'NO'}")
                if par == R.PAR[v]:
                    p(f"      segnali (esposizione W3.2 → ridotta): {det or '—'}")
                rows.append(dict(asset=a, periodo=per, variante=v, par=str(par), tipo=tag, toccate=len(hit),
                                 su=nl if lato > 0 else ns, invariate=same, anni=yrs, segnali=[t["signal"] for t in hit]))
    pd.DataFrame(rows).to_csv(HERE / "conteggi.csv", index=False)
    return rows


def obiettivo(rows):
    """Copertura dei due casi da cui nasce l'idea (già noti dall'analisi delle perdite, IS descrittivo)."""
    p("\n=== COPERTURA DEI DUE CASI-GUIDA (noti dall'analisi errori: BTC long 07/01/2018, ETH long 02/06/2024) ===")
    for r in rows:
        if r["tipo"] != "scelta" or r["variante"] == "D4":
            continue
        k = "2018-01-07" if r["asset"] == "BTC" else "2024-06-02"
        if r["asset"] == "BTC" and r["periodo"] == "dal 2021":
            continue
        p(f"{r['variante']} {r['asset']} {r['periodo']}: caso {k} {'toccato' if k in r['segnali'] else 'NON toccato'}")


def caso_finto():
    """Lezione 101: i vincoli si provano su un caso finto. Serie sintetica (seme 11): strategia a esposizione 1 su un prezzo
    lognormale con deriva; 'dimezzare tutto' (esposizione 0,5 sempre) migliora il CAGR/DD? passa il vincolo sul capitale?"""
    p("\n=== CASO FINTO DEI CRITERI (serie sintetica, nessun dato reale) ===")
    rng = np.random.default_rng(11)
    for mu, sd in ((0.0015, 0.035), (0.0008, 0.035), (0.0025, 0.04)):
        r = rng.normal(mu, sd, 6 * 365)
        out = {}
        for e in (1.0, 0.5):
            eq = np.cumprod(1 + e * r); yrs = len(r) / 365
            dd = float((eq / np.maximum.accumulate(np.maximum(eq, 1)) - 1).min()); cg = eq[-1] ** (1 / yrs) - 1
            out[e] = (eq[-1], cg, dd, cg / abs(dd))
        b, h = out[1.0], out[0.5]
        p(f"deriva {mu:.4f}/g, vol {sd:.3f}: piena fin ×{b[0]:.1f} CAGR/DD {b[3]:.2f} DD {100 * b[2]:.0f}% · dimezzata fin ×{h[0]:.1f}"
          f" CAGR/DD {h[3]:.2f} DD {100 * h[2]:.0f}% → criterio CAGR/DD {'passerebbe' if h[3] > b[3] else 'no'}, DD "
          f"{'passerebbe' if h[2] >= b[2] else 'no'}, capitale −5% {'passerebbe' if h[0] >= 0.95 * b[0] else 'BLOCCA'}")
    p("→ il CAGR/DD da solo può premiare una riduzione indiscriminata (dipende da deriva e volatilità); il vincolo sul capitale "
      "insieme (≥ −5%) e il placebo a pari numero di operazioni ridotte sono i controlli contro l'effetto scala.")


if __name__ == "__main__":
    pd.set_option("display.width", 200)
    buchi(); quote(); rows = conteggi(); obiettivo(rows); caso_finto()
    (HERE / "conteggi_output.txt").write_text("\n".join(LOG) + "\n")
