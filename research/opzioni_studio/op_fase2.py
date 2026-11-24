"""Opzioni · fase 2 · rendimenti secondo PREREG + ADDENDUM-1. Uso: python3 research/opzioni_studio/op_fase2.py

Ordine: cancello (op_cancello) → riconteggio di c ed f con la IV della superficie → F1, F2, F3 (+ "call sempre",
"straddle sempre"), F4, spread a debito → scelta solo su IS → giudizio OOS (5 criteri, "utile" per F3) → diagnosi →
risultati.txt, griglia_F1.csv, uscite_F2.csv, segnali_F3.csv, operazioni_*.csv, placebo.csv, equity.csv.
Ogni periodo (dal 2018, dal 2021, IS 2018–21, OOS 2022–26) è una simulazione separata che parte da 10.000 $ e da flat.
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(ROOT))
import op_count as K  # noqa: E402
import op_engine as E  # noqa: E402
import op_segnali as S  # noqa: E402
import superficie as SU  # noqa: E402
from op_cancello import main as cancello  # noqa: E402
from op_prezzatore import PrezzatoreSuperficie  # noqa: E402
from radar import cone as CONE  # noqa: E402
from radar import weekly as W  # noqa: E402

OUT: list[str] = []
LAST = "2026-11-21"
DAYS = pd.date_range("2018-01-01", LAST)
PER = {"dal 2018": ("2018-01-01", None), "dal 2021": ("2021-01-01", None),
       "IS 2018–21": ("2018-01-01", "2021-12-31"), "OOS 2022–26": ("2022-01-01", None)}
COLS = ["finale", "cagr", "dd", "n", "quota_guadagno", "pf", "peggiore", "serie_peggiore", "senza_2_migliori"]
PZ: PrezzatoreSuperficie | None = None


def say(s: str = "") -> None:
    print(s, flush=True)
    OUT.append(s)


# ------------------------------------------------------------------ esecuzione di una cella in tutti i periodi
def corri(conf: E.Conf, piano: E.Piano, nome: str, store: dict) -> dict:
    out = {}
    for k, (da, a) in PER.items():
        r = E.Motore(PZ, conf).simula(piano, DAYS, da, a)
        out[k] = r
    store[nome] = out
    return out


def met(r: dict) -> dict:
    return E.metriche(r)


def riga(nome: str, rr: dict) -> dict:
    d = {"cella": nome}
    for k, r in rr.items():
        m = met(r)
        for c in COLS:
            d[f"{k} · {c}"] = m.get(c)
    return d


def fmt(m: dict) -> str:
    if not m:
        return "—"
    pf = "—" if m.get("pf") is None else f"{m['pf']:.2f}"
    qg = "—" if m.get("quota_guadagno") is None else f"{m['quota_guadagno']:.0%}"
    pg = "—" if m.get("peggiore") is None else f"{m['peggiore']:+.1%}"
    return (f"{m['finale']:>9,.0f} $ CAGR {m['cagr']:+6.1%} DD {m['dd']:6.1%} op {m['n']:>3} vinc {qg:>4} PF {pf:>5} "
            f"pegg {pg:>6} serie {m['serie_peggiore']:+6.1%} s2m {m['senza_2_migliori']:>8,.0f}")


def tabella(titolo: str, store: dict, nomi: list[str]) -> None:
    say("")
    say(f"== {titolo}")
    for k in PER:
        say(f"-- {k}")
        for n in nomi:
            say(f"{n:<40} {fmt(met(store[n][k]))}")


# ------------------------------------------------------------------ riferimenti
class Rif:
    def __init__(self, trades, equity):
        self.d = {"trades": trades, "equity": equity, "conf": E.Conf()}


def w32_rif(f: pd.DataFrame, lev: float) -> dict:
    out = {}
    for k, (da, a) in PER.items():
        ff = f[f.index <= pd.Timestamp(a)] if a else f
        r = W.simulate(ff, start=da, capital=10_000.0, lev=lev)
        tr = [dict(entry=pd.Timestamp(t["entry"]), exit=pd.Timestamp(t["exit"]), ret=t["pnl"], lato=1 if t["side"] == "long" else -1,
                   motivo=t["reason"]) for t in r["trades"]]
        if r["open"]:
            tr.append(dict(entry=pd.Timestamp(r["open"]["entry"]), exit=ff.index[-1], ret=r["open"]["pnl_close"],
                           lato=1 if r["open"]["side"] == "long" else -1, motivo="aperta"))
        e = r["equity"]
        e = e[(e.index >= pd.Timestamp(da)) & (e.index <= pd.Timestamp(a or LAST))]
        out[k] = Rif(tr, e).d
    return out


def liquidita() -> dict:
    return {k: Rif([], pd.Series(10_000.0, DAYS[(DAYS >= pd.Timestamp(da)) & (DAYS <= pd.Timestamp(a or LAST))])).d
            for k, (da, a) in PER.items()}


def buy_hold(f: pd.DataFrame) -> dict:
    out = {}
    for k, (da, a) in PER.items():
        c = f["close"][(f.index >= pd.Timestamp(da)) & (f.index <= pd.Timestamp(a or LAST))]
        out[k] = Rif([], 10_000 * c / f["open"][c.index[0]]).d
    return out


# ------------------------------------------------------------------ F4: W3.2 a metà su perp senza stop + opzione di protezione
def f4(f: pd.DataFrame, da: str, a: str | None, mny: float = 0.10) -> dict:
    ff = f[(f.index <= pd.Timestamp(a)) if a else f.index == f.index]
    w = W.weekly_bars(ff[ff["close"].notna()])
    days = DAYS[(DAYS >= pd.Timestamp(da)) & ((DAYS <= pd.Timestamp(a)) if a else True)]
    O, C, FU = ff["open"], ff["close"], ff["funding"].fillna(0)
    m = E.Motore(PZ, E.Conf(giorni=30))
    cash, qty, cost, side, pend, opt, trades = 10_000.0, 0.0, 0.0, 0, None, None, []
    eq = np.full(len(days), np.nan)
    cur = None
    for i, d in enumerate(days):
        if pend is not None:                                       # 00:00 lunedì: esecuzione della decisione domenicale
            if pend[0] == "exit" and side:
                px = O[d] * (1 - W.SLIP * side)
                cash += qty * px - cost - abs(qty) * px * W.FEE_PERP
                if opt is not None:                                 # opzione venduta alle 12:00 dello stesso giorno
                    cash += m._sell(d, [g for g in opt["legs"] if g["open"]], PZ.spot(d))
                    opt = None
                cur.update(exit=d, ret=cash / cur["eq0"] - 1, motivo=pend[1])
                trades.append(cur)
                cur, qty, cost, side = None, 0.0, 0.0, 0
            elif pend[0] == "enter" and not side:
                side, wk = pend[1], pend[2]
                lt = 0.5 * W.exposure(side, wk["close"], wk["atr"])
                px = O[d] * (1 + W.SLIP * side)
                qty = side * lt * cash / px
                cost = qty * px
                cur = dict(entry=d, lato=side, eq0=cash, rinnovi=0)
                cash -= abs(qty) * px * W.FEE_PERP
            pend = None
        if side and opt is not None and any(g["open"] and g["exp"] == d for g in opt["legs"]):   # 08:00 scadenza
            cash += m._settle(opt, d)
            opt = None
            cur["rinnovi"] += 1
        if side and opt is None:                                   # 12:00: protezione (o rinnovo) 10% fuori, ≈30 giorni
            opt = m._open(d, -side, cash, mny=mny, qty_btc=abs(qty))
            if opt is not None:
                cash -= opt["spend"]
        if side:
            cash -= qty * C[d] * FU[d]
        mark = m._liq(d, [g for g in opt["legs"] if g["open"]], PZ.spot(d)) if opt is not None else 0.0
        eq[i] = cash + (qty * C[d] - cost if side else 0.0) + mark
        if d.dayofweek == 6 and d in w.index:
            dd = W._decide(w.loc[d], side)
            pend = dd + (w.loc[d], d) if dd else None
    if side:
        trades.append(dict(cur, exit=days[-1], ret=eq[-1] / cur["eq0"] - 1, motivo="aperta"))
    return {"trades": trades, "equity": pd.Series(eq, days), "conf": E.Conf()}


# ------------------------------------------------------------------ segnali F3 con la superficie
def iv30_superficie(w: pd.DataFrame) -> pd.Series:
    out = {}
    for d in w.index:
        sc = SU.scadenza_vicina(d.date(), 30)
        if sc is None:
            continue
        F = PZ.spot(d)
        ks = PZ.strikes(d, pd.Timestamp(sc))
        Kk = min(ks, key=lambda k: abs(k - F)) if ks else F
        v, q = SU.iv(d.date(), sc, Kk, "C", F=F, ora=12.0)
        if q != "mancante":
            out[d] = v
    return pd.Series(out)


def cono_rapporti(f: pd.DataFrame, w: pd.DataFrame, giorni: int = 30) -> pd.DataFrame:
    """F3.f: per ogni lunedì il contratto che il motore comprerebbe (call e put alla pari), costo dalla superficie del lunedì,
    valore atteso a scadenza dal cono con la storia fino alla domenica e orizzonte = giorni alla scadenza."""
    hist = CONE.history(f)
    m = E.Motore(PZ, E.Conf(giorni=giorni))
    rows = {}
    for sun in w.index:
        mon = sun + E.DAY
        if mon > pd.Timestamp(LAST):
            break
        ch = m.scegli(mon, "C", 0.0)
        if ch is None:
            continue
        exp, Kk, S0 = ch
        h = hist[hist.index <= sun]
        p = CONE.prepare(h)
        hz = max(int(round(m.giorni(mon, exp) + 0.5)), 1)
        end, _, _ = CONE.simulate(p["zr"], p["zu"], p["zd"], p["sigma"], p["drift"], S.CONE_PATHS, CONE.SEED, hz)
        ST = p["price"] * np.exp(end)
        r = {}
        for t in ("C", "P"):
            mid, q = PZ.prezzo(mon, exp, Kk, t)
            if mid is None or mid <= 0:
                continue
            pay = np.maximum(ST - Kk, 0) if t == "C" else np.maximum(Kk - ST, 0)
            ev = float(np.mean(pay - np.minimum(E.EXER * ST, E.FEE_CAP * pay)))
            r[t] = ev / (mid * 1.03 + min(0.0003 * S0, 0.125 * mid))
        rows[sun] = {"rC": r.get("C", np.nan), "rP": r.get("P", np.nan), "giorni": hz}
    return pd.DataFrame.from_dict(rows, orient="index")


def f_serie(r: pd.DataFrame, thr: float, idx) -> pd.Series:
    c_ok, p_ok = r["rC"] >= thr, r["rP"] >= thr
    s = np.where(c_ok & p_ok, np.where(r["rC"] >= r["rP"], 1, -1), np.where(c_ok, 1, np.where(p_ok, -1, 0)))
    return pd.Series(s, r.index).reindex(idx).fillna(0).astype(int)


def c_serie(w: pd.DataFrame, iv: pd.Series, mode: str = "c5") -> pd.Series:
    ivs = iv.reindex(w.index)
    pct = S._pct_rank(iv.dropna(), 52).reindex(w.index)
    ok = ivs.notna()
    c1, c3 = ok & (ivs < w["rv30"]), pct <= 0.2
    b = {"c5": c1 | c3, "c1": c1, "c3": c3}[mode]
    return 2 * b.astype(int)


# ------------------------------------------------------------------ test statistici
def p_appaiato(ra: list[dict], rb: list[dict], n: int = 10_000, seed: int = 3) -> float:
    """Stesse operazioni (stessa data d'ingresso): test a segni casuali sulle differenze di log(1+ret), unilaterale."""
    a = {t["entry"]: math.log1p(t["ret"]) for t in ra if t.get("motivo") != "aperta"}
    b = {t["entry"]: math.log1p(t["ret"]) for t in rb if t.get("motivo") != "aperta"}
    common = sorted(set(a) & set(b))
    if not common:
        return float("nan")
    dlt = np.array([a[k] - b[k] for k in common])
    obs = dlt.sum()
    rng = np.random.default_rng(seed)
    sims = (rng.choice([-1, 1], size=(n, len(dlt))) * dlt).sum(axis=1)
    return float((sims >= obs).mean())


def corr_sett(ra: dict, rb: dict) -> float:
    a = ra["equity"].resample("W-SUN").last().pct_change()
    b = rb["equity"].resample("W-SUN").last().pct_change()
    x = pd.concat([a, b], axis=1).dropna()
    return float(x.iloc[:, 0].corr(x.iloc[:, 1])) if len(x) > 5 else float("nan")


def senza2(r: dict) -> float:
    return met(r)["senza_2_migliori"]


# ------------------------------------------------------------------ main
def main() -> None:
    global PZ
    out, ok = cancello()
    OUT.extend(out)
    if not ok:
        (HERE / "risultati.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")
        return
    PZ = PrezzatoreSuperficie()
    f = S.frame()
    f = f[f.index <= LAST]
    w = pd.read_csv(HERE / "cache" / "op_settimanale.csv", index_col=0, parse_dates=True)
    w = w[(w.index >= "2018-01-01") & (w.index <= LAST)]
    tr = pd.read_csv(HERE / "cache" / "op_w32_trades.csv")
    pw = E.piano_w32(tr, DAYS)
    store: dict = {}

    # ---------------- 1. riconteggio c ed f con la superficie
    iv = iv30_superficie(w)
    rr30 = cono_rapporti(f, w, 30)
    w32pos = S.w32_in_pos(tr, DAYS, pd.Timestamp(LAST))
    i0 = len(OUT)
    say("")
    say("== RICONTEGGIO c ed f con la IV della superficie (soglie dell'ADDENDUM-1, non cambiate)")
    say(f"IV superficie alla domenica: {iv.index[0].date()} → {iv.index[-1].date()} ({len(iv)} settimane); "
        f"quintile a 52 sett. dal {S._pct_rank(iv, 52).first_valid_index().date()}")
    cnt = {}
    for nome, s in (("c5 (ADDENDUM)", c_serie(w, iv, "c5")), ("c1 IV < RV30", c_serie(w, iv, "c1")),
                    ("c3 quintile basso", c_serie(w, iv, "c3")), ("f ≥ 1,4 (ADDENDUM)", f_serie(rr30, 1.4, w.index)),
                    ("f ≥ 1,3", f_serie(rr30, 1.3, w.index)), ("f ≥ 1,5", f_serie(rr30, 1.5, w.index))):
        st = K.stats(K.occupa(s, pd.Timestamp(LAST)), s, w32pos, DAYS)
        cnt[nome] = st
        say(f"{nome:<22} op {st['n']:>3} · IS {st['IS']:>3} · OOS {st['OOS']:>3} · lati IS {st['IS_lati']} OOS {st['OOS_lati']} · "
            f"tempo {st['tempo_in_pos']:.2f} · con W3.2 {st['con_w32_in_pos']:.2f}")
    say(f"Rapporto cono/costo con la superficie: call mediana {rr30['rC'].median():.2f} (≥1 nel {(rr30['rC'] >= 1).mean():.0%}), "
        f"put mediana {rr30['rP'].median():.2f} (≥1 nel {(rr30['rP'] >= 1).mean():.0%})")
    c_giud = cnt["c5 (ADDENDUM)"]["IS"] >= 20
    f_giud = cnt["f ≥ 1,4 (ADDENDUM)"]["IS"] >= 20 and cnt["f ≥ 1,4 (ADDENDUM)"]["OOS"] >= 20
    say(f"c giudicabile (IS ≥ 20): {'sì' if c_giud else 'no → descrittivo'} · f con ≥ 20 per metà: {'sì' if f_giud else 'no'}")
    base = (HERE / "cache" / "conteggi_fase1.txt").read_text(encoding="utf-8")
    (HERE / "conteggi.txt").write_text(base + "\n== RICONTEGGIO (fase 2) con la IV della superficie, soglie invariate\n"
                                       + "\n".join(OUT[i0 + 2:]) + "\n", encoding="utf-8")

    # ---------------- 2. riferimenti
    store["W3.2 intera"] = w32_rif(f, 1.0)
    store["W3.2 a metà"] = w32_rif(f, 0.5)
    store["Liquidità"] = liquidita()
    store["Buy & hold"] = buy_hold(f)
    corri(E.Conf(), pw, "B0", store)

    # ---------------- F1
    TEN, MNY = (14, 30, 60, 90), (-0.05, 0.0, 0.05, 0.10)
    lab = lambda g, x: f"F1 {g}g {'alla pari' if x == 0 else f'{abs(x):.0%} ' + ('fuori' if x > 0 else 'dentro')}"  # noqa: E731
    for g in TEN:
        for x in MNY:
            n = lab(g, x)
            if (g, x) == (30, 0.0):
                store[n] = store["B0"]
            else:
                corri(E.Conf(giorni=g, mny=x), pw, n, store)
    f1 = [lab(g, x) for g in TEN for x in MNY]
    # ---------------- F2 (+ vicini)
    f2 = {"F2 U0 come B0": E.Conf(), "F2 U1 vendita a 2×": E.Conf(uscita="U1"), "F2 U2 vendita a 3×": E.Conf(uscita="U2"),
          "F2 U3 metà a 2×": E.Conf(uscita="U3"), "F2 U4 7 giorni prima": E.Conf(uscita="U4"),
          "F2 U5 un rinnovo": E.Conf(uscita="U5")}
    vic2 = {"F2 U1 vendita a 2×": [E.Conf(uscita="U1", u_mult=1.5), E.Conf(uscita="U1", u_mult=2.5)],
            "F2 U2 vendita a 3×": [E.Conf(uscita="U2", u_mult=2.5), E.Conf(uscita="U2", u_mult=3.5)],
            "F2 U3 metà a 2×": [E.Conf(uscita="U3", u_mult=1.5), E.Conf(uscita="U3", u_mult=2.5)],
            "F2 U4 7 giorni prima": [E.Conf(uscita="U4", u4_giorni=5), E.Conf(uscita="U4", u4_giorni=10)],
            "F2 U5 un rinnovo": [E.Conf(uscita="U5", giorni=21), E.Conf(uscita="U5", giorni=45)]}
    for n, c in f2.items():
        if n == "F2 U0 come B0":
            store[n] = store["B0"]
        else:
            corri(c, pw, n, store)
    for n, cs in vic2.items():
        for j, c in enumerate(cs):
            corri(c, pw, f"{n} · vicino {j + 1}", store)
    # ---------------- spread a debito (descrittivi)
    for k in (0.15, 0.20):
        corri(E.Conf(spread_k=k), pw, f"Spread a debito: alla pari − {k:.0%} fuori", store)

    # ---------------- F3
    sig = {"F3a tendenza": w["a_pend"], "F3b flusso W3.2 ogni settimana": w["b_0"], "F3c volatilità bassa → straddle": c_serie(w, iv),
           "F3d compressione → straddle": 2 * (w["bbw_pct52"] <= 0.2).astype(int),
           "F3e dopo cascata → call": (w["min_ret_cc"] <= -0.10).astype(int), "F3f cono ≥ 1,4 × costo": f_serie(rr30, 1.4, w.index),
           "Rif. call sempre": pd.Series(1, w.index), "Rif. straddle sempre": pd.Series(2, w.index)}
    for n, s in sig.items():
        corri(E.Conf(), E.piano_settimanale(s), n, store)
    rr21, rr45 = cono_rapporti(f, w, 21), cono_rapporti(f, w, 45)
    vic3 = {"F3a tendenza": [("a2", E.Conf(), w["a_pos"]), ("21g", E.Conf(giorni=21), w["a_pend"]),
                             ("45g", E.Conf(giorni=45), w["a_pend"]), ("5% fuori", E.Conf(mny=0.05), w["a_pend"])],
            "F3c volatilità bassa → straddle": [("c1", E.Conf(), c_serie(w, iv, "c1")), ("c3", E.Conf(), c_serie(w, iv, "c3")),
                                                ("21g", E.Conf(giorni=21), c_serie(w, iv)), ("45g", E.Conf(giorni=45), c_serie(w, iv))],
            "F3f cono ≥ 1,4 × costo": [("1,3", E.Conf(), f_serie(rr30, 1.3, w.index)), ("1,5", E.Conf(), f_serie(rr30, 1.5, w.index)),
                                        ("21g", E.Conf(giorni=21), f_serie(rr21, 1.4, w.index)),
                                        ("45g", E.Conf(giorni=45), f_serie(rr45, 1.4, w.index))]}
    for n, lst in vic3.items():
        for lab3, c, s in lst:
            corri(c, E.piano_settimanale(s), f"{n} · vicino {lab3}", store)
    # ---------------- F4
    store["F4 W3.2 metà su perp + protezione 10% fuori"] = {k: f4(f, da, a) for k, (da, a) in PER.items()}

    # ---------------- tabelle
    tabella("RIFERIMENTI", store, ["W3.2 intera", "W3.2 a metà", "Liquidità", "Buy & hold", "B0"])
    tabella("F1 · struttura (scadenza × prezzo d'esercizio), uscite come B0", store, f1)
    tabella("F2 · uscite sul contratto di B0", store, list(f2))
    tabella("F3 · segnali indipendenti (conto separato per segnale)", store, list(sig))
    tabella("F4 e spread a debito (descrittivi)", store, ["F4 W3.2 metà su perp + protezione 10% fuori",
                                                          "Spread a debito: alla pari − 15% fuori", "Spread a debito: alla pari − 20% fuori"])
    pd.DataFrame([riga(n, store[n]) for n in f1]).to_csv(HERE / "griglia_F1.csv", index=False)
    pd.DataFrame([riga(n, store[n]) for n in list(f2) + [k for k in store if k.startswith("F2 ") and "vicino" in k]]) \
        .to_csv(HERE / "uscite_F2.csv", index=False)
    pd.DataFrame([riga(n, store[n]) for n in list(sig) + [k for k in store if k.startswith("F3") and "vicino" in k]]) \
        .to_csv(HERE / "segnali_F3.csv", index=False)

    # ---------------- 3. scelta su IS e giudizio OOS
    B = {k: met(store["B0"][k]) for k in PER}
    say("")
    say("== SCELTA SOLO SU IS (massimo capitale finale IS con DD IS non peggiore di B0 di oltre 3 punti) E GIUDIZIO OOS")
    verdetti = []

    def giudica(fam, nome, vicini, m_holm, p_raw, f3=False, placebo_p=None, n_is=None, n_oos=None):
        mo = met(store[nome]["OOS 2022–26"])
        c1 = mo["finale"] > B["OOS 2022–26"]["finale"] and mo["dd"] >= B["OOS 2022–26"]["dd"] - 0.03
        c2 = mo["senza_2_migliori"] > B["OOS 2022–26"]["senza_2_migliori"]
        vs = [met(store[v]["OOS 2022–26"])["finale"] > B["OOS 2022–26"]["finale"] for v in vicini]
        c3 = len(vs) > 0 and np.mean(vs) >= 0.75
        c4 = (n_is >= 20 and n_oos >= 20 and placebo_p is not None and placebo_p <= 0.05) if f3 else None
        p_holm = min(1.0, p_raw * m_holm) if p_raw == p_raw else float("nan")
        c5 = p_holm <= 0.05
        tutti = c1 and c2 and c3 and c5 and (c4 if f3 else True)
        verdetti.append(dict(famiglia=fam, cella=nome, finale_OOS=mo["finale"], dd_OOS=mo["dd"], B0_OOS=B["OOS 2022–26"]["finale"],
                             c1_finale_dd=c1, c2_senza2=c2, c3_vicini=f"{sum(vs)}/{len(vs)}", c4_f3=c4, p=p_raw, p_holm=p_holm,
                             c5_holm=c5, migliore_di_B0=tutti))
        say(f"{fam} · {nome}: OOS {mo['finale']:,.0f} $ DD {mo['dd']:.1%} contro B0 {B['OOS 2022–26']['finale']:,.0f} $ DD "
            f"{B['OOS 2022–26']['dd']:.1%} → (1) {'sì' if c1 else 'no'} · (2) senza le 2 migliori {mo['senza_2_migliori']:,.0f} contro "
            f"{B['OOS 2022–26']['senza_2_migliori']:,.0f} {'sì' if c2 else 'no'} · (3) vicini {sum(vs)}/{len(vs)} "
            f"{'sì' if c3 else 'no'} · " + (f"(4) op IS/OOS {n_is}/{n_oos}, placebo p {placebo_p} {'sì' if c4 else 'no'} · " if f3 else "")
            + f"(5) p {p_raw:.3f}, Holm ×{m_holm} = {p_holm:.3f} {'sì' if c5 else 'no'} → "
            + ("MIGLIORE DI B0" if tutti else "non migliore di B0"))
        return tutti

    def scegli_is(nomi):
        ok = [n for n in nomi if met(store[n]["IS 2018–21"])["dd"] >= B["IS 2018–21"]["dd"] - 0.03]
        return max(ok, key=lambda n: met(store[n]["IS 2018–21"])["finale"]) if ok else None

    # F1
    s1 = scegli_is(f1)
    say(f"F1: scelta su IS = {s1} (IS {met(store[s1]['IS 2018–21'])['finale']:,.0f} $, DD {met(store[s1]['IS 2018–21'])['dd']:.1%}; "
        f"B0 IS {B['IS 2018–21']['finale']:,.0f} $, DD {B['IS 2018–21']['dd']:.1%})")
    if s1 == "F1 30g alla pari":
        say("F1: la cella scelta è B0 stessa → nessun cambio di struttura proposto")
        verdetti.append(dict(famiglia="F1", cella=s1, migliore_di_B0=False, nota="scelta IS = B0"))
    else:
        g0 = next(g for g in TEN if lab(g, 0) == s1 or any(lab(g, x) == s1 for x in MNY))
        x0 = next(x for x in MNY if lab(g0, x) == s1)
        ti, xi = TEN.index(g0), MNY.index(x0)
        vic = [lab(TEN[ti + dt], MNY[xi + dx]) for dt, dx in ((1, 0), (-1, 0), (0, 1), (0, -1))
               if 0 <= ti + dt < len(TEN) and 0 <= xi + dx < len(MNY)]
        giudica("F1", s1, vic, len(f1) - 1, p_appaiato(store[s1]["OOS 2022–26"]["trades"], store["B0"]["OOS 2022–26"]["trades"]))
    # F2
    s2 = scegli_is(list(f2))
    say(f"F2: scelta su IS = {s2} (IS {met(store[s2]['IS 2018–21'])['finale']:,.0f} $, DD {met(store[s2]['IS 2018–21'])['dd']:.1%})")
    if s2 == "F2 U0 come B0":
        say("F2: la cella scelta è B0 stessa → nessun cambio d'uscita proposto")
        verdetti.append(dict(famiglia="F2", cella=s2, migliore_di_B0=False, nota="scelta IS = B0"))
    else:
        giudica("F2", s2, [f"{s2} · vicino 1", f"{s2} · vicino 2"], len(f2) - 1,
                p_appaiato(store[s2]["OOS 2022–26"]["trades"], store["B0"]["OOS 2022–26"]["trades"]))
    # F3: placebo e criteri
    say("")
    say("== F3 · placebo (1.000 estrazioni di lunedì a caso in OOS, stesso numero e stessa sequenza di lati, stessa durata)")
    plac_rows, giud3 = [], {"F3a tendenza": True, "F3c volatilità bassa → straddle": c_giud, "F3f cono ≥ 1,4 × costo": True}
    p3 = {}
    for n in ["F3a tendenza", "F3c volatilità bassa → straddle", "F3f cono ≥ 1,4 × costo", "Rif. call sempre"]:
        rr = store[n]["OOS 2022–26"]
        pl = E.placebo(E.Motore(PZ, E.Conf()), rr, DAYS, n=1000, seed=11, da="2022-01-01")
        p3[n] = pl["p"]
        plac_rows += [dict(cella=n, estrazione=i, finale=v, reale=pl["reale"]) for i, v in enumerate(pl["finali"])]
        say(f"{n}: reale {pl['reale']:,.0f} $ · placebo mediana {np.median(pl['finali']):,.0f} $, 95° pct "
            f"{np.quantile(pl['finali'], .95):,.0f} $ · p = {pl['p']:.3f}")
    pd.DataFrame(plac_rows).to_csv(HERE / "placebo.csv", index=False)
    say("")
    say("== F3 · giudizio OOS (migliore di B0: 5 criteri; utile: OOS > 10.000 $, PF ≥ 1,2, punti 2–5, correlazione settimanale con B0 < 0,5)")
    n3 = 6
    for n in ["F3a tendenza", "F3c volatilità bassa → straddle", "F3f cono ≥ 1,4 × costo"]:
        mi, mo = met(store[n]["IS 2018–21"]), met(store[n]["OOS 2022–26"])
        vic = [f"{n} · vicino {l3}" for l3, _, _ in vic3[n]]
        if not giud3[n]:
            say(f"{n}: descrittivo (IS < 20 operazioni con la superficie)")
        best = giudica("F3", n, vic, n3, p3[n], f3=True, placebo_p=p3[n], n_is=mi["n"], n_oos=mo["n"])
        cor = corr_sett(store[n]["OOS 2022–26"], store["B0"]["OOS 2022–26"])
        vs = [met(store[v]["OOS 2022–26"])["finale"] > 10_000 for v in vic]
        ut = (mo["finale"] > 10_000 and (mo["pf"] or 0) >= 1.2 and mo["senza_2_migliori"] > 10_000 and np.mean(vs) >= 0.75
              and mi["n"] >= 20 and mo["n"] >= 20 and p3[n] <= 0.05 and min(1, p3[n] * n3) <= 0.05 and cor < 0.5 and giud3[n])
        v = verdetti[-1]
        v.update(utile=ut, corr_B0=round(cor, 2), pf_OOS=mo["pf"], n_IS=mi["n"], n_OOS=mo["n"])
        say(f"   utile? OOS {mo['finale']:,.0f} $ · PF {mo['pf']} · senza le 2 migliori {mo['senza_2_migliori']:,.0f} $ · vicini sopra "
            f"10.000 {sum(vs)}/{len(vs)} · placebo p {p3[n]:.3f} (Holm ×{n3} {min(1, p3[n] * n3):.3f}) · corr. B0 {cor:.2f} → "
            + ("UTILE" if ut else "non utile"))
        if n == "F3f cono ≥ 1,4 × costo":
            cs = met(store["Rif. call sempre"]["OOS 2022–26"])
            say(f"   riserva ADDENDUM: f contro 'call sempre' in OOS: {mo['finale']:,.0f} $ contro {cs['finale']:,.0f} $ → "
                + ("f la batte" if mo["finale"] > cs["finale"] else "f NON la batte"))
    pd.DataFrame(verdetti).to_csv(HERE / "verdetti.csv", index=False)

    # ---------------- 4. diagnosi
    diagnosi(store, w, iv, ["B0", s1, s2, "F3a tendenza", "F3c volatilità bassa → straddle", "F3f cono ≥ 1,4 × costo"], pw, sig)
    # equity
    eqs = {n: store[n]["dal 2018"]["equity"] for n in ["B0", "W3.2 intera", "W3.2 a metà", "Buy & hold", s1, s2,
                                                       "F3a tendenza", "F3c volatilità bassa → straddle", "F3f cono ≥ 1,4 × costo",
                                                       "Rif. call sempre", "F4 W3.2 metà su perp + protezione 10% fuori"]}
    pd.DataFrame(eqs).round(2).to_csv(HERE / "equity.csv")
    q = PZ.qual
    tot = sum(q.values())
    say("")
    say("Qualità dei prezzi usati (tutte le chiamate, valutazioni giornaliere comprese): "
        + ", ".join(f"{k} {v / tot:.1%}" for k, v in q.most_common()))
    (HERE / "risultati.txt").write_text("\n".join(OUT) + "\n", encoding="utf-8")


def ops_df(r: dict, iv: pd.Series | None = None) -> pd.DataFrame:
    rows = []
    for t in r["trades"]:
        g = t["legs"][0] if "legs" in t else {}
        ql = [q for x in t.get("legs", []) for q in x.get("qual", [])]
        rows.append(dict(entra=t["entry"].date(), esce=t["exit"].date(), lato=t["lato"], motivo=t.get("motivo"),
                         scadenza=g.get("exp").date() if g else None, giorni=t.get("giorni_scad"), K=g.get("K"),
                         S0=round(t.get("S0", np.nan), 0), spesa=round(t.get("spend", np.nan), 2), mult=round(t.get("mult", np.nan), 3),
                         ret_conto=round(t["ret"], 4),
                         qual_ingresso=g.get("qual", [None])[0] if g else None,
                         quota_non_scambi=round(np.mean([q != "scambi" for q in ql]), 3) if ql else None))
    return pd.DataFrame(rows)


def diagnosi(store, w, iv, nomi, pw, sig) -> None:
    say("")
    say("== DIAGNOSI (dal 2018)")
    ivw = iv.reindex(pd.date_range(iv.index[0], LAST)).ffill()
    terz = ivw.quantile([1 / 3, 2 / 3]).to_numpy()
    for n in dict.fromkeys(nomi):
        r = store[n]["dal 2018"]
        d = ops_df(r)
        safe = "".join(ch if ch.isalnum() else "_" for ch in n)[:40]
        d.to_csv(HERE / f"operazioni_{safe}.csv", index=False)
        dd = d[d["motivo"] != "aperta"]
        if dd.empty:
            continue
        say(f"-- {n}: {len(dd)} operazioni chiuse")
        b = dd.sort_values("ret_conto")
        say("   migliori: " + "; ".join(f"{x.entra} {x.lato:+d} {x.ret_conto:+.1%}" for x in b.tail(3)[::-1].itertuples()))
        say("   peggiori: " + "; ".join(f"{x.entra} {x.lato:+d} {x.ret_conto:+.1%}" for x in b.head(3).itertuples()))
        lg = np.log1p(dd["ret_conto"])
        yr = lg.groupby(pd.to_datetime(dd["entra"]).dt.year).sum()
        say("   per anno (rendimento composto delle operazioni): " + " ".join(f"{y}:{math.expm1(v):+.0%}" for y, v in yr.items()))
        sd = lg.groupby(dd["lato"]).agg(["count", "sum"])
        say("   per lato: " + " · ".join(f"{ {1: 'call', -1: 'put', 2: 'straddle'}[k]} n {int(v['count'])} {math.expm1(v['sum']):+.0%}"
                                         for k, v in sd.iterrows()))
        reg = pd.cut([ivw.get(pd.Timestamp(e), np.nan) for e in dd["entra"]], [-1, terz[0], terz[1], 99],
                     labels=["IV bassa", "IV media", "IV alta"])
        rg = lg.groupby(np.asarray(reg)).agg(["count", "sum"])
        say("   per regime di IV all'ingresso (terzili 2018–26): " + " · ".join(f"{k} n {int(v['count'])} {math.expm1(v['sum']):+.0%}"
                                                                           for k, v in rg.iterrows()))
        say(f"   prezzo d'ingresso non da 'scambi': {(dd['qual_ingresso'] != 'scambi').mean():.0%} · quota media di valutazioni "
            f"interpolate/estese: {dd['quota_non_scambi'].mean():.0%} · giorni alla scadenza: mediana {dd['giorni'].median():.0f} "
            f"(min {dd['giorni'].min():.0f}, max {dd['giorni'].max():.0f})")
    say("")
    say("== SENSIBILITÀ AI COSTI (differenza denaro-lettera per lato; commissioni invariate), dal 2018 e OOS")
    cand = {"B0": (E.Conf(), pw)}
    for n, s in sig.items():
        if n.startswith(("F3a", "F3c", "F3f")):
            cand[n] = (E.Conf(), E.piano_settimanale(s))
    for n, (c, p) in cand.items():
        parts = []
        for sp in (0.0, 0.03, 0.06):
            c2 = E.con(c, spread=sp)
            a = met(E.Motore(PZ, c2).simula(p, DAYS, "2018-01-01"))
            o = met(E.Motore(PZ, c2).simula(p, DAYS, "2022-01-01"))
            parts.append(f"{sp:.0%}: {a['finale']:,.0f} / {o['finale']:,.0f} $")
        say(f"{n:<34} " + " · ".join(parts))
    # anni 2018 per B0: scadenze lontane dal bersaglio
    d0 = ops_df(store["B0"]["dal 2018"])
    say("")
    say("B0, giorni alla scadenza per operazione: " + ", ".join(f"{x.entra}: {x.giorni:.0f}" for x in d0.itertuples()))


if __name__ == "__main__":
    main()
