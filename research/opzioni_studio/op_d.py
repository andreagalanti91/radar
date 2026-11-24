"""Opzioni · secondo ciclo (ADDENDUM-2 D) · descrittivi per chi opera a mano su B0r (nessuna regola nuova).

1. Ritardo d'ingresso di 0 / 12 / 24 / 48 / 72 ore dal lunedì 00:00 UTC: contratto della regola (venerdì più vicino a 30 giorni
   fra 20 e 50, prezzo d'esercizio più vicino sulla griglia) scelto e prezzato all'istante d'ingresso con la superficie del
   giorno e F = prezzo Binance di quell'ora; uscita come B0r (stesso istante d'uscita o scadenza).
2. Ingresso solo se BTC all'istante d'ingresso è entro ±3% dalla chiusura settimanale del segnale, contro ingresso comunque.
3. Ricampionamento: 10.000 estrazioni con reinserimento dei moltiplicatori di B0r (operazioni chiuse dal 2018) su 3 anni
   (numero di operazioni come nello storico): conto al 5% composto, probabilità di perdita, serie peggiore di premi persi;
   gli stessi numeri con 1.500 e 2.000 $ fissi per operazione.
Conto = 10.000 × Π(1 + 0,05 (m − 1)) sulle operazioni chiuse (l'operazione aperta del 16/11 è esclusa).
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import op_engine as E  # noqa: E402
import superficie as SU  # noqa: E402
from op_prezzatore import PrezzatoreSuperficie  # noqa: E402

FIN = (20, 50)
OUT: list[str] = []


def say(s=""):
    print(s, flush=True)
    OUT.append(s)


def main() -> list[str]:
    pz = PrezzatoreSuperficie()
    h1 = pd.read_csv(HERE / "cache" / "btc_1h.csv", index_col=0, parse_dates=True)["open"]
    h1 = h1.reindex(pd.date_range(h1.index[0], h1.index[-1], freq="h")).interpolate("time")
    tr = pd.read_csv(HERE / "cache" / "op_w32_trades.csv")
    days = pd.date_range("2018-01-01", "2026-11-21")
    base = E.Motore(pz, E.Conf(finestra=FIN)).simula(E.piano_w32(tr, days), days, "2018-01-01")
    sig_close = {pd.Timestamp(x["entry"]): float(x["sig_close"]) if "sig_close" in x else np.nan for _, x in tr.iterrows()}
    w = pd.read_csv(HERE / "cache" / "op_settimanale.csv", index_col=0, parse_dates=True)["close"]
    ops = []   # (ingresso lunedì, lato, istante d'uscita o None, scadenza B0r non usata)
    for _, x in tr.iterrows():
        if not isinstance(x["exit"], str):
            continue                               # aperta: esclusa
        d0 = pd.Timestamp(x["entry"])
        ex = pd.Timestamp(x["exit"])
        t_exit = ex + pd.Timedelta(hours=12) + (E.DAY if x["reason"] not in ("ema", "dist") else pd.Timedelta(0))
        ops.append(dict(d0=d0, lato=1 if x["side"] == "long" else -1, t_exit=t_exit, sig=float(w[d0 - E.DAY])))

    def mult(op, delay_h: int):
        t0 = op["d0"] + pd.Timedelta(hours=delay_h)
        if t0 >= op["t_exit"]:
            return None, None
        d, hr = t0.normalize(), t0.hour
        F = float(h1[t0])
        tipo = "C" if op["lato"] > 0 else "P"
        cand = [pd.Timestamp(e) for e in SU.scadenze(d.date()) if e.weekday() == 4]
        gg = lambda e: ((e + pd.Timedelta(hours=8)) - t0).total_seconds() / 86400  # noqa: E731
        cand = [e for e in cand if FIN[0] <= gg(e) <= FIN[1]]
        if not cand:
            return None, F
        exp = min(cand, key=lambda e: (abs(gg(e) - 30), -e.value))
        ks = pz.strikes(d, exp)
        K = min(ks, key=lambda k: (abs(k - F), k)) if ks else round(F / E.griglia_default(F)) * E.griglia_default(F)
        P0, q = SU.prezzo(d.date(), exp.date(), K, tipo, F=F, ora=hr)
        if not np.isfinite(P0) or P0 <= 0:
            return None, F
        cost = P0 * 1.03 + min(0.0003 * F, 0.125 * P0)
        if exp + pd.Timedelta(hours=8) <= op["t_exit"]:
            ST = pz.regolamento(exp)
            iv = max(ST - K, 0) if tipo == "C" else max(K - ST, 0)
            val = iv - min(0.0002 * ST, 0.125 * iv)
        else:
            d1 = op["t_exit"].normalize()
            S1 = pz.spot(d1)
            P1, _ = SU.prezzo(d1.date(), exp.date(), K, tipo, F=S1, ora=12.0)
            val = P1 * 0.97 - min(0.0003 * S1, 0.125 * P1)
        return max(val, 0) / cost, F

    def conto(ms):
        return 10_000 * float(np.prod([1 + 0.05 * (m - 1) for m in ms]))

    say("== D.1 · RITARDO D'INGRESSO su B0r (operazioni chiuse; uscita invariata) e D.2 · soglia del 3% dalla chiusura del segnale")
    say(f"{'ritardo':<10}{'op':>4}{'conto 2018':>12}{'conto 2021':>12}{'OOS 22–26':>12} | {'op ≤3%':>7}{'conto 2018':>12}"
        f"{'conto 2021':>12}{'OOS':>10}  mosse oltre il 3%")
    res = {}
    for dl in (0, 12, 24, 48, 72):
        rows = []
        for op in ops:
            m, F = mult(op, dl)
            if m is None:
                continue
            mv = op["lato"] * (F / op["sig"] - 1)
            rows.append(dict(d0=op["d0"], m=m, mossa=mv, ok3=abs(F / op["sig"] - 1) <= 0.03))
        d = pd.DataFrame(rows)
        res[dl] = d
        p = lambda x, a: x[x["d0"] >= a]  # noqa: E731
        k3 = d[d["ok3"]]
        say(f"{dl:>3} ore   {len(d):>4}{conto(d['m']):>12,.0f}{conto(p(d, '2021')['m']):>12,.0f}{conto(p(d, '2022')['m']):>12,.0f} | "
            f"{len(k3):>7}{conto(k3['m']):>12,.0f}{conto(p(k3, '2021')['m']):>12,.0f}{conto(p(k3, '2022')['m']):>10,.0f}  "
            + ", ".join(f"{r.d0.date()} {r.mossa:+.1%} (m {r.m:.2f})" for r in d[~d["ok3"]].itertuples()))
    say("(mossa = movimento a favore del segnale fra la chiusura della domenica e l'ingresso; l'operazione 'saltata' con la soglia")
    say(" perde il suo moltiplicatore m, che nella colonna 'op ≤3%' non entra nel conto)")
    # motore contro calcolo per operazione a 12 ore
    eng = [t["mult"] for t in base["trades"] if t["motivo"] != "aperta"]
    say(f"Controllo: a 12 ore il calcolo per operazione dà {conto(res[12]['m']):,.0f} $, il motore (B0r) {conto(eng):,.0f} $")

    say("")
    say("== D.3 · RICAMPIONAMENTO dei moltiplicatori di B0r su 3 anni (10.000 estrazioni con reinserimento)")
    m = np.array(eng)
    yrs = (pd.Timestamp("2026-11-21") - pd.Timestamp("2018-01-01")).days / 365.25
    n3 = int(round(len(m) / yrs * 3))
    rng = np.random.default_rng(2026)
    draws = m[rng.integers(0, len(m), size=(10_000, n3))]
    acc = 10_000 * np.prod(1 + 0.05 * (draws - 1), axis=1)

    def serie(row, unit):
        worst = cur = 0.0
        for x in row:
            cur = cur + unit(x) if x < 1 else 0.0
            worst = min(worst, cur)
        return worst

    q = lambda a: " / ".join(f"{v:,.0f}" for v in np.quantile(a, [.05, .25, .5, .75, .95]))  # noqa: E731
    say(f"Moltiplicatori di partenza: {len(m)} operazioni chiuse dal 2018 (mediana {np.median(m):.2f}, in perdita {np.mean(m < 1):.0%}, "
        f"premio perso del tutto {np.mean(m == 0):.0%}); {n3} operazioni in 3 anni")
    say(f"Conto al 5% composto da 10.000 $ · percentili 5/25/50/75/95: {q(acc)} $ · probabilità di chiudere sotto 10.000 $: "
        f"{np.mean(acc < 10_000):.1%}")
    nl = np.array([max((len(s) for s in "".join("L" if x < 1 else "W" for x in r).split("W")), default=0) for r in draws])
    sp = np.array([serie(r, lambda x: np.log1p(0.05 * (x - 1))) for r in draws])
    say(f"Serie peggiore di operazioni in perdita consecutive: mediana {np.median(nl):.0f}, 95° percentile {np.quantile(nl, .95):.0f}; "
        f"perdita composta della serie: mediana {np.expm1(np.median(sp)):.1%}, 5° percentile {np.expm1(np.quantile(sp, .05)):.1%}")
    for amt in (1500, 2000):
        pnl = (amt * (draws - 1)).sum(axis=1)
        ws = np.array([serie(r, lambda x: amt * (x - 1)) for r in draws])
        say(f"{amt:,} $ fissi per operazione: risultato in 3 anni (5/25/50/75/95): {q(pnl)} $ · probabilità di perdita "
            f"{np.mean(pnl < 0):.1%} · serie peggiore di premi persi: mediana {np.median(ws):,.0f} $, 5° percentile "
            f"{np.quantile(ws, .05):,.0f} $ · perdita massima per operazione {amt:,} $")
    hist = {a: float((a * (m - 1)).sum()) for a in (1500, 2000)}
    say(f"Nello storico (dal 2018, {len(m)} operazioni): 1.500 $ fissi → {hist[1500]:+,.0f} $; 2.000 $ fissi → {hist[2000]:+,.0f} $")
    (HERE / "descrittivi_D.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
    return OUT


if __name__ == "__main__":
    main()
