"""dati_nuovi · FASE 1 · inventario delle fonti e CONTEGGI (nessun rendimento di varianti).
- periodo, buchi, ritardo applicato per ogni fonte; controlli incrociati fra fonti gemelle (correlazioni descrittive);
- distribuzione del segnale s alle domeniche;
- quanti ingressi di W3.2 (traiettoria base) cadrebbero con s contrario (A), quante domeniche/episodi da flat soddisfano la regola
  B (condizioni di prezzo vere, flusso col segno sbagliato, fonte nel verso). Solo numeri di eventi, nessun esito.
Uscita: conteggi_output.txt
"""
from __future__ import annotations

import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fonti as F  # noqa: E402
import motore as M  # noqa: E402

LOG = []


def p(*a):
    s = " ".join(str(x) for x in a); print(s); LOG.append(s)


def gaps(idx, freq_days=1):
    idx = pd.DatetimeIndex(sorted(set(pd.DatetimeIndex(idx).normalize())))
    g = pd.Series(idx[1:] - idx[:-1], index=idx[1:]).dt.days
    big = g[g > freq_days]
    return len(big), int(big.max()) if len(big) else 0, [f"{(d - pd.Timedelta(days=int(n))).date()}→{d.date()}" for d, n in big.sort_values().tail(3).items()]


def inventory():
    p("=== INVENTARIO FONTI (dati grezzi scaricati) ===")
    D = F.D
    for a in ("BTC", "ETH"):
        x = F.cot_level(a)
        n, mx, ex = gaps(x["report"], 7)
        late = sum(((x["report"] >= s) & (x["report"] <= e)).sum() for s, e, _ in F.COT_LATE)
        p(f"COT {a} CME (TFF, settimanale): {x['report'].min().date()} → {x['report'].max().date()}, {len(x)} report; salti > 7 gg: {n} "
          f"(max {mx} gg); ritardo: martedì → venerdì (+3 gg), {late} report in finestre di shutdown con pubblicazione ritardata")
    for a in ("BTC", "ETH"):
        q = pd.read_csv(D / "basis" / f"deribit_{a}_quarterly.csv", parse_dates=["t"])
        pp = pd.read_csv(D / "basis" / f"deribit_{a}_perp.csv", parse_dates=["t"])
        b = F.basis_daily(a)
        n, mx, ex = gaps(b.index)
        p(f"BASE {a} Deribit: trimestrali {q['inst'].nunique()} ({q['t'].min().date()} → {q['t'].max().date()}), perpetual "
          f"{pp['t'].min().date()} → {pp['t'].max().date()}; base calcolabile {b.index.min().date()} → {b.index.max().date()} "
          f"({len(b)} gg, buchi {n}, max {mx} gg {ex}); mediana {100 * b.median():.1f}% annuo, p5/p95 {100 * b.quantile(.05):.1f}/{100 * b.quantile(.95):.1f}%")
        bn = pd.read_csv(D / "basis" / f"binance_cm_{a}_quarterly.csv", parse_dates=["t"])
        p(f"     Binance coin-M trimestrali (controllo): {bn['inst'].nunique()} contratti, {bn['t'].min().date()} → {bn['t'].max().date()}")
    for a in ("BTC", "ETH"):
        df, avg = F.funding_daily(a, M.frame(a, a == "BTC")["funding"])
        parts = ", ".join(f"{c} {df[c].first_valid_index().date()}→{df[c].last_valid_index().date()}" for c in df)
        cr = df.dropna().corr().round(2)
        p(f"FUNDING {a}: {parts}; media disponibile dal {avg.first_valid_index().date()}; correlazioni giornaliere "
          + "; ".join(f"{i}-{j} {cr.loc[i, j]}" for k, i in enumerate(cr.index) for j in cr.columns[k + 1:]))
        for ex in ("okx", "bitget"):
            z = pd.read_csv(D / "funding" / f"{ex}_{a}.csv")
            t = pd.to_datetime(z["fundingTime"].astype("int64"), unit="ms")
            p(f"     {ex} {a}: solo API recente {t.min().date()} → {t.max().date()} ({len(z)} pagamenti) → non usabile nel backtest")
    h = pd.read_csv(D / "miner" / "hash-rate.csv", parse_dates=["date"])
    n, mx, ex = gaps(h["date"])
    p(f"MINER blockchain.com: hash-rate {h['date'].min().date()} → {h['date'].max().date()} ({len(h)} gg, buchi {n}, max {mx} gg); "
      f"anche difficulty, miners-revenue, transaction-fees-usd; ritardo applicato 2 gg")
    cm = F._cm("BTC")
    hh = h.set_index("date")["hash-rate"]
    j = pd.concat([hh, cm["HashRate"]], axis=1).dropna().loc["2018":]
    p(f"     controllo: correlazione hash rate blockchain.com vs CoinMetrics dal 2018 (SMA30) "
      f"{j.rolling(30).mean().corr().iloc[0, 1]:.3f}")
    for a in ("BTC", "ETH"):
        c = F._cm(a)
        st = c["FlowInExNtv-status"].value_counts().to_dict()
        p(f"CM FLUSSI {a}: FlowIn/FlowOut/SplyEx {c.dropna(subset=['FlowInExNtv']).index.min().date()} → {c.index.max().date()} "
          f"({len(c)} gg); stato delle righe {st} → tutte 'flash' anche nel passato: storico ricalcolato, NON point-in-time")


def sundays(a, b):
    return pd.date_range(a, b, freq="W-SUN")


def counts():
    p("\n=== SEGNALI ALLE DOMENICHE (quota di settimane con s = +1 / 0 / −1) ===")
    out = {}
    for a, st, lg in (("BTC", "2018-01-01", True), ("ETH", "2021-01-11", False)):
        f = M.frame(a, lg)
        sig = {
            "COT": F.cot_signal(a), "BASE": F.basis_signal(a), "FUNDING": F.funding_signal(a, f["funding"]),
            "FUNDING-B": F.funding_signal_b(a, f["funding"]), "MINER": F.hash_signal(), "MINER-B(E)": F.hash_signal_b(), "CM-A netflow7": F.cm_netflow_signal(a), "CM-B saldo28": F.cm_balance_signal(a),
        }
        out[a] = (f, st, sig)
        su = sundays(st, M.END)
        for k, s in sig.items():
            v = s.reindex(su).fillna(0)
            first = s[s != 0].first_valid_index()
            p(f"{a} {k:14s} primo segnale ≠ 0: {first.date() if first is not None else '-'} · domeniche {len(su)}: "
              f"+1 {100 * (v == 1).mean():.0f}% · 0 {100 * (v == 0).mean():.0f}% · −1 {100 * (v == -1).mean():.0f}%")
    p("\n=== CONTEGGI SULLA TRAIETTORIA BASE DI W3.2 (nessun esito) ===")
    for a, (f, st, sig) in out.items():
        o = M.sim(f, st)
        base = o["trades"] + ([o["open"]] if o["open"] else [])
        w = o["weekly"]
        pl, ps = M.price_conds(w)
        pos = pd.Series(0, index=w.index)
        for t in base:
            e = pd.Timestamp(t["entry"]); x = pd.Timestamp(t["exit"]) if t.get("exit") else w.index[-1] + pd.Timedelta(days=7)
            pos[(pos.index >= e - pd.Timedelta(days=1)) & (pos.index < x - pd.Timedelta(days=1))] = 1
        flat = (pos == 0) & (w.index >= pd.Timestamp(st) - pd.Timedelta(days=1))
        opp = (flat & ((pl & (w["flow"] <= 0)) | (ps & (w["flow"] >= 0)))).sum()
        p(f"{a}: ingressi base {len(base)} ({sum(t['side'] == 'long' for t in base)} long, {sum(t['side'] == 'short' for t in base)} short); "
          f"domeniche da flat con prezzo ok e flusso contrario (spazio per B): {int(opp)}")
        for k, s in sig.items():
            g = s.reindex(w.index).fillna(0)
            blk = sum(1 for t in base if g.get(pd.Timestamp(t["signal"]), 0) == (-1 if t["side"] == "long" else 1))
            if k.startswith("MINER-B"):           # regola E: ingresso anticipato senza SMA40 né flusso
                el = flat & ((w["close"] > w["ema21"]) & (w["ema20"] > w["ema20"].shift(1))).fillna(False) & (g == 1) & ~(w["long"])
                ep = lambda m: int((m & ~m.shift(1, fill_value=False)).sum())  # noqa: E731
                p(f"   {k:14s} E: domeniche candidate long in più rispetto a W3.2 {int(el.sum())} (episodi {ep(el)})")
                continue
            bl = flat & pl & (w["flow"] <= 0) & (g == 1)
            bs = flat & ps & (w["flow"] >= 0) & (g == -1)
            ep = lambda m: int((m & ~m.shift(1, fill_value=False)).sum())  # noqa: E731
            p(f"   {k:14s} A: ingressi base con fonte contraria {blk}/{len(base)} · B: domeniche candidate long {int(bl.sum())} "
              f"(episodi {ep(bl)}), short {int(bs.sum())} (episodi {ep(bs)})")
        # controllo del motore: con s ≡ 0 le regole A e B non cambiano nulla
        z = pd.Series(0, index=F.IDX)
        e0 = o["equity"].iloc[-1]
        ok = all(abs(M.sim(f, st, z, m)["equity"].iloc[-1] - e0) < 1e-6 for m in ("A", "B", "E"))
        p(f"   controllo: regole A/B/E con fonte neutra identiche alla base: {ok}")


if __name__ == "__main__":
    inventory()
    counts()
    (HERE / "conteggi_output.txt").write_text("\n".join(LOG) + "\n")
