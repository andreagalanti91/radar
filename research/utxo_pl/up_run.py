"""Fase 3 · H1–H4 del PREREG (bdada1a). Uso: python3 up_run.py (~ pochi minuti) -> risultati.txt, trade_cambiati.csv,
placebo.csv, h4_trade.csv. Dati: research/p2_nuovi/data congelati al 15/11/2026 (stessi degli studi su W3.2: 78.474 $) per
il giudizio; data/ del repo (fino al 21/11/2026) solo per lo short aperto il 16/11/2026."""
from __future__ import annotations

import sys
import warnings
from pathlib import Path

import numpy as np
import pandas as pd

warnings.filterwarnings("ignore")
HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT / "research" / "p2_nuovi"))
import up_engine as E  # noqa: E402
from p2_data import load  # noqa: E402
from radar import weekly as W  # noqa: E402
from radar.data import load_all  # noqa: E402
from radar.features import build_features  # noqa: E402

NPL, BLK = int(__import__("os").environ.get("NPL", 1000)), 30
RNG = np.random.default_rng(20261125)
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s, flush=True)
    OUT.append(s)


d = load()
F, FL = d["f"], d["fl"]
FV = build_features(load_all())
FV = FV[FV["close"].notna()]
Z = E.zones(E.load_mvrv())
# Periodi del verdetto come scritti nel PREREG ("dal 2018-01-01 e dal 2021-01-01"); 2018-20 come controllo aggiuntivo
# (correzione 25/11: la prima esecuzione giudicava su 2018-20 invece che dal 2018).
PER = {"2018+": (FL, "2018-01-01", None), "2021+": (F, "2021-01-01", None), "2018-20": (FL, "2018-01-01", "2020-12-31")}
VERD = ("2018+", "2021+")
INFO = {"2021+ IS 21-23": (F, "2021-01-01", "2023-12-31"),
        "2021+ OOS 24-26": (F, "2024-01-01", None)}
WB = {k: W.weekly_bars((x[x.index <= e] if e else x)[lambda y: y["close"].notna()]) for k, (x, s, e) in {**PER, **INFO}.items()}


def tl(r):
    return list(r["trades"]) + ([dict(r["open"], pnl=r["open"]["pnl_close"], exit=None, exit_px=None, reason="aperto")]
                                if r["open"] else [])


def met(r):
    e = r["equity"] / r["equity"].iloc[0]
    yrs = (e.index[-1] - e.index[0]).days / 365.25
    dd = float((e / e.cummax() - 1).min())
    cagr = float(e.iloc[-1] ** (1 / yrs) - 1)
    pn = np.array([t["pnl"] for t in tl(r)]) if tl(r) else np.zeros(0)
    return dict(fin=round(10000 * float(e.iloc[-1])), cagr=round(100 * cagr, 1), dd=round(100 * dd, 1),
                cdd=round(cagr / abs(dd), 3) if dd < 0 else None, n=len(pn),
                wr=round(100 * float((pn > 0).mean()), 1) if len(pn) else None)


def bh(x, s, e):
    x = x[(x.index >= s) & ((x.index <= e) if e else True)]
    eq = x["close"] / (x["open"].iloc[0] * (1 + W.SLIP) * (1 + W.FEE_SPOT))
    dd = float((eq / eq.cummax() - 1).min())
    return dict(fin=round(10000 * float(eq.iloc[-1])), dd=round(100 * dd, 1))


def run(per, rule=None, dfn="b", cap=None, eup=None, src=None):
    x, s, e = (src or {**PER, **INFO})[per]
    if cap is None and eup is None and rule:
        cap, eup = Z[f"cap_{dfn}"], Z[f"eup_{dfn}"]
    return E.simulate(x, start=s, end=e, rule=rule, cap=cap, eup=eup, w=WB.get(per))


def fm(m):
    return f"{m['fin']:>7,} $ · CAGR {m['cagr']:5.1f}% · DD {m['dd']:6.1f}% · C/DD {m['cdd']} · trade {m['n']:2d} · WR {m['wr']}%"


def groups(rv, rb):
    """Δ log per trade W3.2: i trade della variante con ingresso dentro [ingresso, uscita] di un trade W3.2 si sommano a quel
    trade; quelli fuori da ogni finestra formano il gruppo "nuovi"."""
    bt, vt = tl(rb), tl(rv)
    out, used = {}, set()
    for b in bt:
        a, z = b["entry"], b["exit"] or "9999"
        mine = [j for j, v in enumerate(vt) if a <= v["entry"] <= z and v["side"] == b["side"]]
        used |= set(mine)
        out[(b["entry"], b["side"])] = (b, [vt[j] for j in mine],
                                        sum(np.log1p(vt[j]["pnl"]) for j in mine) - np.log1p(b["pnl"]))
    rest = [v for j, v in enumerate(vt) if j not in used]
    if rest:
        out[("nuovi", "")] = (None, rest, sum(np.log1p(v["pnl"]) for v in rest))
    return out


def placebo(per, rule, mask, real_fin):
    x, s, e = PER[per]
    ix = x[(x.index >= s) & ((x.index <= e) if e else True)].index
    n = int(mask.reindex(ix).fillna(False).sum())
    if n == 0:
        return n, None, None
    vals = []
    for _ in range(NPL):
        m = np.zeros(len(ix), bool)
        while m.sum() < n:
            st = RNG.integers(0, len(ix) - 1)
            m[st:st + BLK] = True
        k = np.flatnonzero(m)[n:]       # tronca all'esatto numero di giorni-zona
        m[k] = False
        ms = pd.Series(m, ix)
        r = run(per, rule, cap=ms, eup=ms)
        vals.append(met(r)["fin"])
    vals = np.array(vals)
    return n, float(np.median(vals)), float((vals >= real_fin).mean())


# ------------------------------------------------------------------ 0. verifica del motore
say("== 0. Verifica: motore copia senza regola = radar.weekly.simulate ==")
for per, (x, s, e) in {**PER, "live 2021+ (data/ al 21/11)": (FV, "2021-01-01", None)}.items():
    xx = x[x.index <= e] if e else x
    ra, rb = W.simulate(xx, start=s), E.simulate(x, start=s, end=e)
    same = (len(ra["trades"]) == len(rb["trades"]) and all(abs(p["pnl"] - q["pnl"]) < 1e-12 and p["exit"] == q["exit"]
            for p, q in zip(ra["trades"], rb["trades"])) and abs(ra["equity"].iloc[-1] - rb["equity"].iloc[-1]) < 1e-6)
    say(f"{per}: identico {same} · finale {rb['equity'].iloc[-1]:,.0f} $ · trade chiusi {len(rb['trades'])} · aperto "
        f"{(rb['open'] or {}).get('side')} {(rb['open'] or {}).get('entry')} {(rb['open'] or {}).get('entry_px')}")
    assert same
assert round(met(run("2021+"))["fin"]) == 78474

BASE = {p: run(p) for p in {**PER, **INFO}}
say("\n== 1. Riferimenti ==")
for p in {**PER, **INFO}:
    x, s, e = {**PER, **INFO}[p]
    say(f"W3.2 {p:16s} {fm(met(BASE[p]))} | buy & hold {bh(x, s, e)}")

# ------------------------------------------------------------------ 2. H1–H3
rows_t, rows_v, rows_p = [], [], []
say("\n== 2. H1–H3 (sostituto MVRV) ==")
for rule in ("H1", "H2", "H3"):
    for dfn in ("a", "b"):
        crit = {1: True, 2: True, 3: True}
        for per in PER:
            rv, rb = run(per, rule, dfn), BASE[per]
            mv, mb = met(rv), met(rb)
            g = groups(rv, rb)
            ch = {k: v for k, v in g.items() if abs(v[2]) > 1e-9}
            c1 = mv["fin"] > mb["fin"] and mv["dd"] >= mb["dd"] - 2
            if ch:
                kmax = max(ch, key=lambda k: abs(ch[k][2]))
                wo = mv["fin"] / np.exp(ch[kmax][2])
            else:
                kmax, wo = None, mv["fin"]
            # togliere l'unico trade cambiato riporta esattamente a W3.2: non è un miglioramento. Tolleranza 5 $ (correzione
            # 25/11: con round() l'arrotondamento del finale dava "True" anche a parità esatta con W3.2)
            c2 = wo - mb["fin"] > 5
            side_m = Z[f"cap_{dfn}"] if rule in ("H1", "H2") else Z[f"eup_{dfn}"]
            n, med, p = placebo(per, rule, side_m, mv["fin"])
            c3 = p is not None and p <= 0.05
            if per in VERD:
                crit[1] &= c1; crit[2] &= c2; crit[3] &= c3
            say(f"{rule}({dfn}) {per:8s} {fm(mv)} | Δ fin {mv['fin']-mb['fin']:+,} · Δ DD {mv['dd']-mb['dd']:+.1f} | "
                f"c1 {c1} · c2 {c2} (senza {kmax}: {wo:,.0f}) · c3 {c3} (giorni-zona {n}, placebo mediana {med}, p {p})"
                + (f" · short bloccati {rv['blocked']}" if rv["blocked"] else ""))
            rows_v.append(dict(regola=rule, definizione=dfn, periodo=per, **mv, delta_fin=mv["fin"] - mb["fin"],
                               c1=c1, c2=c2, c3=c3, giorni_zona=n, placebo_mediana=med, placebo_p=p))
            rows_p.append(dict(regola=rule, definizione=dfn, periodo=per, giorni_zona=n, osservato=mv["fin"], mediana=med, p=p))
            for (k, sd), (b, vs, dl) in ch.items():
                say(f"     {sd or k} {k}: W3.2 " + (f"{b['entry']} @{b['entry_px']:,.0f} → {b['exit']} @{b['exit_px'] or 0:,.0f} "
                    f"({b['reason']}) {100*b['pnl']:+.1f}%" if b else "—") + " | regola: " +
                    ("; ".join(f"{v['entry']} @{v['entry_px']:,.0f} → {v['exit']} @{(v['exit_px'] or 0):,.0f} ({v['reason']}) "
                               f"{100*v['pnl']:+.1f}%" for v in vs) or "nessun trade") +
                    f" | Δ log {100*dl:+.1f} pt ≈ {mb['fin']*(np.exp(dl)-1):+,.0f} $ sul finale")
                rows_t.append(dict(regola=rule, definizione=dfn, periodo=per, trade_w32=k, lato=sd,
                                   w32_uscita=b["exit"] if b else None, w32_px=b["exit_px"] if b else None,
                                   w32_pnl=round(100 * b["pnl"], 2) if b else None,
                                   regola_trade="; ".join(f"{v['entry']}→{v['exit']}@{v['exit_px']}" for v in vs),
                                   regola_pnl=round(100 * (np.prod([1 + v["pnl"] for v in vs]) - 1), 2) if vs else 0.0,
                                   delta_log_pt=round(100 * dl, 2), delta_usd=round(mb["fin"] * (np.exp(dl) - 1))))
        say(f"  → {rule}: criteri sui due periodi del PREREG 2018+ e 2021+ ({dfn}): 1 {crit[1]} · 2 {crit[2]} · 3 {crit[3]}")
        rows_v.append(dict(regola=rule, definizione=dfn, periodo="CRITERI", c1=crit[1], c2=crit[2], c3=crit[3]))

say("\n== 2b. Informativo (non nel verdetto): IS/OOS del 2021+ ==")
for rule in ("H1", "H2", "H3"):
    for dfn in ("a", "b"):
        say(f"{rule}({dfn}) " + " | ".join(f"{p}: {met(run(p, rule, dfn))['fin']:,} (W3.2 {met(BASE[p])['fin']:,}, "
                                           f"DD {met(run(p, rule, dfn))['dd']})" for p in INFO))

say("\n== 2c. Informativo: H1 senza riaperture (H1+H2) e parametri vicini di (b) per H1 ==")
for per in {**PER, **INFO}:
    m0 = met(BASE[per])
    parts = [f"H1+H2(a) {met(run(per, 'H1+H2', 'a'))['fin']:,}", f"H1+H2(b) {met(run(per, 'H1+H2', 'b'))['fin']:,} "
             f"DD {met(run(per, 'H1+H2', 'b'))['dd']}"]
    for win, q in ((1460, 0.05), (1460, 0.15), (730, 0.10), (1095, 0.10)):
        zz = E.zones(E.load_mvrv(), win, q)
        mm = met(run(per, "H1", cap=zz["cap_b"], eup=zz["eup_b"]))
        parts.append(f"H1 b[{win}g,{int(q*100)}%] {mm['fin']:,} DD {mm['dd']}")
    say(f"{per:16s} W3.2 {m0['fin']:,} DD {m0['dd']} | " + " | ".join(parts))

# ------------------------------------------------------------------ 3. short aperto il 16/11/2026 (data/ fino al 21/11)
say("\n== 3. Short del 16/11/2026 (data/ del repo fino al 21/11) ==")
LV = {"live": (FV, "2021-01-01", None)}
rb = E.simulate(FV, start="2021-01-01")
o = rb["open"]
say(f"W3.2: short aperto {o['entry']} @{o['entry_px']:,.2f} · ultima chiusura {o['last']:,.0f} · stop/trailing {o['trail']:,.0f} · "
    f"esposizione {o['expo']}")
for dfn in ("a", "b"):
    rv = E.simulate(FV, start="2021-01-01", rule="H1", cap=Z[f"cap_{dfn}"])
    last = [t for t in rv["trades"] if t["entry"] >= "2026-11-01"]
    rv2 = E.simulate(FV, start="2021-01-01", rule="H1+H2", cap=Z[f"cap_{dfn}"])
    say(f"H1+H2({dfn}) finale {rv2['equity'].iloc[-1]:,.0f} $ · ultimi trade " + "; ".join(
        f"{t['entry']}→{t['exit']} @{t['exit_px']:,.0f} {100*t['pnl']:+.2f}%" for t in rv2["trades"][-2:]))
    say(f"H1({dfn}): " + ("; ".join(f"chiuso {t['exit']} @{t['exit_px']:,.2f} ({t['reason']}) movimento {100*t['move']:+.1f}% "
                                    f"pnl quota {100*t['pnl']:+.2f}%" for t in last) or "non chiuso")
        + f" · pendente {rv['pending']} · finale {rv['equity'].iloc[-1]:,.0f} $ (W3.2 {rb['equity'].iloc[-1]:,.0f} $)")
say(Z.loc["2026-11-14":, ["mvrv", "lo_b", "cap_a", "cap_b"]].round(3).to_string())
say(FV.loc["2026-11-15":, ["open", "high", "low", "close"]].round(0).to_string())

# ------------------------------------------------------------------ 4. H4 descrittiva
say("\n== 4. H4 descrittiva: long 1x dal primo giorno di capitolazione, uscita a euforia o 365 g ==")
h4rows = []
for dfn in ("a", "b"):
    for per, (x, s, e) in {"2018+": (FL, "2018-01-01", None), "2021+": (F, "2021-01-01", None),
                           "2015-26 (FL)": (FL, "2015-01-01", None)}.items():
        r = E.h4(x, Z[f"cap_{dfn}"], Z[f"eup_{dfn}"], s, e)
        eq = r["equity"] / 10000
        dd = float((eq / eq.cummax() - 1).min())
        allt = r["trades"] + ([r["open"]] if r["open"] else [])
        wr = 100 * np.mean([t["pnl"] > 0 for t in allt]) if allt else float("nan")
        say(f"H4({dfn}) {per}: finale {10000*eq.iloc[-1]:,.0f} $ · DD {100*dd:.1f}% · WR {wr:.0f}% · trade {len(r['trades'])}"
            f"{' + aperto' if r['open'] else ''} | buy & hold {bh(x, s, e)}")
        for t in r["trades"] + ([r["open"]] if r["open"] else []):
            say(f"     {t['entry']} @{t['entry_px']:,.0f} → {t.get('exit', 'aperto')} @{t.get('exit_px', t.get('last', 0)):,.0f} "
                f"{100*t['pnl']:+.1f}%")
            h4rows.append(dict(definizione=dfn, periodo=per, ingresso=t["entry"], px_in=round(t["entry_px"]),
                               uscita=t.get("exit"), px_out=round(t.get("exit_px", t.get("last", 0))), pnl=round(100 * t["pnl"], 1)))

pd.DataFrame(rows_v).to_csv(HERE / "varianti.csv", index=False)
pd.DataFrame(rows_t).to_csv(HERE / "trade_cambiati.csv", index=False)
pd.DataFrame(rows_p).to_csv(HERE / "placebo.csv", index=False)
pd.DataFrame(h4rows).to_csv(HERE / "h4_trade.csv", index=False)
(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
