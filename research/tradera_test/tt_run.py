"""tradera_test · fase 2: esegue PREREG.md (commit 9da09c8). Output: risultati.txt, trade.csv, varianti.csv.
Uso: python3 tt_run.py [--quick]   (--quick: 200 estrazioni placebo invece di 1.000, solo per prove)"""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402
import tt_bt as B  # noqa: E402
import tt_detect as T  # noqa: E402

NDRAW = 200 if "--quick" in sys.argv else 1000
SEED = 20261123
OUT, ROWS = [], []
U2 = fetch.U2
PER = {"azioni": {"A": ("2016-01-01", "2020-12-31"), "B": ("2021-01-01", "2026-11-20")},
       "crypto": {"A": ("2018-01-01", "2020-12-31"), "B": ("2021-01-01", "2026-11-22")}}
SUB = {"21-23": ("2021-01-01", "2023-12-31"), "24-26": ("2024-01-01", "2026-11-22")}
FUND = {"azioni": (0.05, 0.01), "crypto": (0.0, 0.0)}
PPY = {"azioni": 252, "crypto": 365}


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


def load() -> dict:
    fr = {n: fetch.stock(n).loc["2012-01-01":] for n in U2 + ["LMT", "NVDA"]}
    fr["BTC"] = fetch.crypto("BTCUSDT")
    fr["ETH"] = fetch.crypto("ETHUSDT")
    return {k: v[v["close"].notna()] for k, v in fr.items()}


def market(a: str) -> str:
    return "crypto" if a in ("BTC", "ETH", "BTC4h") else "azioni"


def rs_rank(frames: dict, names: list[str]) -> pd.DataFrame:
    c = pd.DataFrame({n: frames[n]["close"] for n in names}).sort_index().ffill()
    r = (c.pct_change(21).rank(axis=1, pct=True) + c.pct_change(63).rank(axis=1, pct=True)) / 2
    # con 2 asset i ranghi sono 0,5 e 1: normalizzo in [0, 1] (il più forte 1, il più debole 0)
    n = c.notna().sum(axis=1)
    return (r * n.values[:, None] - 1).div((n - 1).clip(lower=1), axis=0)


def build(frames: dict, p: dict | None = None) -> dict:
    """Segnali per asset (ritest e piano speculare) + array per il placebo."""
    S = {}
    for a, df in frames.items():
        r = T.detect(df, p)
        ema200 = r["ema"][200]
        reg = df["close"].to_numpy(float) > ema200
        for s in r["signals"]:
            s["kind"] = "ritest"
        for s in r["flips"]:
            s["kind"] = "speculare"
        S[a] = dict(sig=[s for s in r["signals"] if s["ok"]], flip=[s for s in r["flips"] if s["rr"] >= T.P["RRMIN"]],
                    allsig=r["signals"], reg=reg, atr=r["atr"], pending=r["pending"],
                    O=df["open"].to_numpy(float), H=df["high"].to_numpy(float), L=df["low"].to_numpy(float),
                    C=df["close"].to_numpy(float), idx=df.index)
    return S


def select(S: dict, a: str, var: str, rs: pd.DataFrame | None) -> list[dict]:
    sig = list(S[a]["sig"])
    if var in ("V2", "V3", "V4", "V2L", "V2S"):
        sig = [s for s in sig if s["conf"]]
    if var == "V4":
        sig = sig + list(S[a]["flip"])
    if var == "V3":
        ix = S[a]["idx"]
        col = rs[a].reindex(ix).to_numpy() if rs is not None and a in rs else np.full(len(ix), np.nan)
        sig = [s for s in sig if np.isfinite(col[s["t"]]) and ((s["side"] > 0 and col[s["t"]] >= 0.5) or
                                                                (s["side"] < 0 and col[s["t"]] <= 0.5))]
    if var in ("V1L", "V2L"):
        sig = [s for s in sig if s["side"] > 0]
    if var in ("V1S", "V2S"):
        sig = [s for s in sig if s["side"] < 0]
    if var == "FLIP":
        sig = S[a]["flipref"]
    return sig


def trades(frames, S, assets, var, per, rs, fund=None):
    out = []
    for a in assets:
        m = market(a)
        st, en = per if isinstance(per, tuple) else PER[m][per]
        f = fund or FUND[m]
        tr = B.trades_from_signals(frames[a], select(S, a, var, rs), st, en, f[0], f[1], PPY[m], a, S[a]["reg"])
        for t in tr:
            t["per"] = per if isinstance(per, str) else "x"
        out += tr
    return out


def equity(frames, tr, assets, per, mode, fund=None):
    m = market(assets[0])
    st, en = per if isinstance(per, tuple) else PER[m][per]
    f = fund or FUND[m]
    if mode == "risk":
        return B.portfolio(tr, {a: frames[a] for a in assets}, st, en, "risk", f, PPY[m])
    curves = []
    for a in assets:
        ta = [t for t in tr if t["asset"] == a]
        curves.append(B.portfolio(ta, {a: frames[a]}, st, en, "full", f, PPY[m]))
    return pd.concat(curves, axis=1).ffill().bfill().mean(axis=1)


def bh(frames, assets, per, fund):
    m = market(assets[0])
    st, en = PER[m][per] if isinstance(per, str) else per
    cs = []
    for a in assets:
        c = frames[a]["close"].loc[st:en]
        r = c.pct_change().fillna(0) - fund / PPY[m]
        cs.append(10000 * (1 + r).cumprod())
    return pd.concat(cs, axis=1).ffill().bfill().mean(axis=1)


def fmt(m):
    return (f"fin {m['fin']:>7,} · CAGR {m['cagr']:>5}% · DD {m['dd']:>6}% · C/DD {m['cdd']:>5} · n {m['n']:>4} · WR {m['wr']:>5}% "
            f"· R medio {m['mR']:>6} · netto/trade {m['mnet']:>5}% · durata {m['dur']:>5} g · ΣR {m['sumR']:>6} · ΣR senza 3 migliori "
            f"{m['sumR_no3']:>6} · R medio senza il migliore {m['mR_no1']}").replace(",", ".")


def arrays_for(S):
    return {a: dict(O=v["O"], H=v["H"], L=v["L"], C=v["C"], reg=v["reg"]) for a, v in S.items()}


def periods_idx(frames, assets, m):
    out = {}
    for p, (st, en) in PER[m].items():
        out[p] = {}
        for a in assets:
            ix = frames[a].index
            out[p][a] = (ix.searchsorted(pd.Timestamp(st)), ix.searchsorted(pd.Timestamp(en), "right") - 1)
    return out


def main():
    frames = load()
    S = build(frames)
    for a in S:
        S[a]["flipref"] = B.flip_signals(frames[a], S[a]["atr"])
    rs = {"azioni": rs_rank(frames, U2), "crypto": rs_rank(frames, ["BTC", "ETH"])}
    MK = {"azioni": U2, "crypto": ["BTC", "ETH"]}
    rng = np.random.default_rng(SEED)
    say(f"=== tradera_test · backtest preregistrato (PREREG 9da09c8) · placebo {NDRAW} estrazioni · parametri {T.P}")
    alltr = []
    verdict = {}
    for m, assets in MK.items():
        say(f"\n######## {m.upper()} ({', '.join(assets)}) ########")
        fund = FUND[m]
        for p in ("A", "B"):
            bhm = B.metrics(bh(frames, assets, p, fund[0]), [])
            say(f"[{m} {PER[m][p][0][:4]}–{PER[m][p][1][:4]}] buy & hold equipesato{' (funding 5%)' if m == 'azioni' else ''}: "
                f"fin {bhm['fin']:,} · CAGR {bhm['cagr']}% · DD {bhm['dd']}% · C/DD {bhm['cdd']}".replace(",", "."))
            ROWS.append(dict(mercato=m, periodo=p, variante="buy&hold", **bhm))
        for var in ("V1", "V2", "V3", "V4", "V1L", "V1S", "V2L", "V2S", "FLIP"):
            res = {}
            for p in ("A", "B"):
                tr = trades(frames, S, assets, var, p, rs[m])
                for mode in ("risk", "full"):
                    eq = equity(frames, tr, assets, p, mode)
                    mt = B.metrics(eq, tr)
                    res[(p, mode)] = (mt, tr)
                    ROWS.append(dict(mercato=m, periodo=p, variante=var, size=mode, **mt))
                    say(f"{var:4s} {p} {'rischio 2%' if mode == 'risk' else 'capitale pieno'}: {fmt(mt)}")
                if var in ("V1", "V2", "V3", "V4", "FLIP"):
                    for t in tr:
                        alltr.append(dict(t, variante=var, mercato=m))
            if var in ("V1", "V2", "V3", "V4", "V1L", "V1S", "V2L", "V2S"):   # L/S: descrittive, fuori dal verdetto
                trA, trB = res[("A", "risk")][1], res[("B", "risk")][1]
                pl = B.placebo(trA + trB, arrays_for(S), periods_idx(frames, assets, m), NDRAW, rng,
                               {a: fund for a in assets}, {a: PPY[m] for a in assets})
                rA = np.mean([t["R"] for t in trA]) if trA else np.nan
                rB = np.mean([t["R"] for t in trB]) if trB else np.nan
                rT = np.mean([t["R"] for t in trA + trB]) if trA + trB else np.nan
                pA = float(np.mean(pl.get("A", np.array([np.nan])) >= rA))
                pB = float(np.mean(pl.get("B", np.array([np.nan])) >= rB))
                pT = float(np.mean(pl["tutti"] >= rT))
                Rs = np.sort([t["R"] for t in trA + trB])[::-1]
                c1 = rA > 0 and rB > 0
                c2 = rA > np.nanmean(pl.get("A", np.nan)) and rB > np.nanmean(pl.get("B", np.nan)) and pT < 0.05 / 6
                c3 = Rs[3:].sum() > 0
                c4 = len(trA) >= 30 and len(trB) >= 30
                v = "funziona" if (c1 and c2 and c3 and c4) else ("non funziona" if (c4 and (not c1 or not c2)) else "non dimostrabile")
                if var in ("V1", "V2", "V3", "V4"):
                    verdict[(m, var)] = v
                say(f"   placebo {var}: R medio reale A {rA:.3f} / B {rB:.3f} / tutti {rT:.3f}; placebo medio A "
                    f"{np.nanmean(pl.get('A', np.nan)):.3f} / B {np.nanmean(pl.get('B', np.nan)):.3f} / tutti {np.nanmean(pl['tutti']):.3f}; "
                    f"p A {pA:.3f} · B {pB:.3f} · tutti {pT:.3f}")
                say(f"   criteri {var}: 1 {'✓' if c1 else '✗'} · 2 {'✓' if c2 else '✗'} · 3 {'✓' if c3 else '✗'} (ΣR senza 3 "
                    f"{Rs[3:].sum():.1f}) · 4 {'✓' if c4 else '✗'} ({len(trA)}/{len(trB)} trade) → {v.upper()}")
                ROWS.append(dict(mercato=m, periodo="placebo", variante=var, pA=pA, pB=pB, pT=pT, verdetto=v))
        # per lato, descrittivo, stessi criteri senza placebo
        for var in ("V2L", "V2S"):
            rr = [np.mean([t["R"] for t in trades(frames, S, assets, var, p, rs[m])] or [np.nan]) for p in ("A", "B")]
            nn = [len(trades(frames, S, assets, var, p, rs[m])) for p in ("A", "B")]
            say(f"   lato {var}: R medio A {rr[0]:.3f} ({nn[0]}) · B {rr[1]:.3f} ({nn[1]})")
        # confluenza e forza relativa: differenza di R medio (bootstrap)
        for a_, b_, nome in (("V2", "V1", "confluenza"), ("V3", "V2", "forza relativa")):
            ta = trades(frames, S, assets, a_, "A", rs[m]) + trades(frames, S, assets, a_, "B", rs[m])
            tb = trades(frames, S, assets, b_, "A", rs[m]) + trades(frames, S, assets, b_, "B", rs[m])
            ka = {(t["asset"], t["sig"]) for t in ta}
            inn = np.array([t["R"] for t in tb if (t["asset"], t["sig"]) in ka])
            out = np.array([t["R"] for t in tb if (t["asset"], t["sig"]) not in ka])
            if len(inn) > 2 and len(out) > 2:
                bs = [rng.choice(inn, len(inn)).mean() - rng.choice(out, len(out)).mean() for _ in range(2000)]
                say(f"   {nome}: trade di {b_} con il filtro R medio {inn.mean():.3f} (n {len(inn)}) contro senza {out.mean():.3f} "
                    f"(n {len(out)}); differenza IC 95% [{np.percentile(bs, 2.5):.3f}, {np.percentile(bs, 97.5):.3f}]")
        # sottoperiodi 2021–23 / 2024–26 per V2
        for nm, per in SUB.items():
            tr = trades(frames, S, assets, "V2", per, rs[m])
            mt = B.metrics(equity(frames, tr, assets, per, "risk"), tr)
            say(f"   V2 {nm} rischio 2%: {fmt(mt)}")
        # per asset (V2, capitale pieno, tutto 2016/2018 → oggi)
        say(f"   per asset V2 (capitale pieno, {PER[m]['A'][0][:4]} → oggi):")
        for a in assets:
            per = (PER[m]["A"][0], PER[m]["B"][1])
            tr = trades(frames, S, [a], "V2", per, rs[m])
            mt = B.metrics(equity(frames, tr, [a], per, "full"), tr)
            b = B.metrics(bh(frames, [a], per, fund[0]), [])
            say(f"     {a:5s} n {mt['n']:3d} · WR {mt['wr']}% · R medio {mt['mR']} · fin {mt['fin']} · DD {mt['dd']}% | b&h fin {b['fin']} DD {b['dd']}%")
            ROWS.append(dict(mercato=m, periodo="tutto", variante="V2", asset=a, size="full", **mt))
    # esempi LMT e NVDA (calibrazione: descrittivi) e portafoglio U2 + esempi
    say("\n######## ESEMPI (usati per calibrare: descrittivi) ########")
    for a in ("LMT", "NVDA"):
        for var in ("V1", "V2"):
            per = ("2016-01-01", "2026-11-20")
            tr = trades(frames, S, [a], var, per, None)
            mt = B.metrics(equity(frames, tr, [a], per, "full"), tr)
            say(f"{a} {var} 2016→oggi capitale pieno: {fmt(mt)}")
    for p in ("A", "B"):
        tr = trades(frames, S, U2 + ["LMT", "NVDA"], "V2", p, rs["azioni"].reindex(columns=U2 + ["LMT", "NVDA"]))
        mt = B.metrics(equity(frames, tr, U2 + ["LMT", "NVDA"], p, "risk"), tr)
        say(f"U2 + LMT + NVDA V2 {p} rischio 2%: {fmt(mt)}")
    # sensibilità funding (azioni, V2) e vicini (V2, R medio per mercato e periodo)
    say("\n######## ROBUSTEZZA ########")
    for fr in (0.0, 0.10):
        for p in ("A", "B"):
            tr = trades(frames, S, U2, "V2", p, rs["azioni"], fund=(fr, 0.01))
            mt = B.metrics(equity(frames, tr, U2, p, "risk", fund=(fr, 0.01)), tr)
            say(f"azioni V2 funding long {fr:.0%} {p}: {fmt(mt)}")
    NEI = dict(PIV5=dict(PIV=5), PIV15=dict(PIV=15), MOM1=dict(MOM=1.0), MOM2=dict(MOM=2.0), TOL025=dict(TOL=0.25),
               INV05=dict(INV=0.5), BASE2=dict(BASE=2), CF05=dict(CF=0.5), CF2=dict(CF=2.0), RR15=dict(RRMIN=1.5), RR3=dict(RRMIN=3.0))
    for nm, q in NEI.items():
        old = dict(T.P)
        T.P.update(q)
        Sq = build(frames)
        T.P.clear()
        T.P.update(old)
        row = []
        for m, assets in MK.items():
            for p in ("A", "B"):
                tr = trades(frames, Sq, assets, "V2", p, rs[m])
                row.append(f"{m} {p} {np.mean([t['R'] for t in tr]) if tr else float('nan'):+.3f} ({len(tr)})")
        say(f"vicino {nm:7s}: " + " · ".join(row))
        ROWS.append(dict(variante="vicino " + nm, riga=" · ".join(row)))
    # BTC 4h
    f4 = fetch.crypto("BTC", "4h")
    f4 = f4[f4["close"].notna()]
    S4 = build({"BTC4h": f4})
    for var in ("V1", "V2"):
        for p in ("A", "B"):
            st, en = PER["crypto"][p]
            tr = B.trades_from_signals(f4, select(S4, "BTC4h", var, None), st, en, 0, 0, 6 * 365, "BTC4h", S4["BTC4h"]["reg"])
            mt = B.metrics(B.portfolio(tr, {"BTC4h": f4}, st, en, "risk", (0, 0), 6 * 365), tr)
            say(f"BTC 4h {var} {p} rischio 2%: {fmt(mt)}")
    pd.DataFrame(alltr).drop(columns=["e", "j"]).to_csv(HERE / "trade.csv", index=False)
    pd.DataFrame(ROWS).to_csv(HERE / "varianti.csv", index=False)
    say("\nVerdetti:", {f"{k[0]} {k[1]}": v for k, v in verdict.items()})
    (HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
