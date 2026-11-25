"""peso_btc_eth · peso del capitale fra BTC ed ETH con W3.2 (PREREG.md, commit c7d618a). Solo numpy/pandas.

Trade da radar.weekly.simulate invariato (via research/w32_asset2/lib.py: csim, cfeats, dati crypto/data), ogni asset con il suo
conto da 10.000 $ che parte flat alla data d'inizio del periodo. Conto unico = w * BTC + (1 - w) * ETH.
Modo A: nessun ribilanciamento (quote che crescono da sole). Modo B: ribilanciamento al peso a ogni 1° gennaio (alla chiusura del
31/12). Uscite: risultati.csv, out.txt. Non scrive fuori da questa cartella."""
from __future__ import annotations
import sys
sys.dont_write_bytecode = True
from pathlib import Path
import numpy as np, pandas as pd

HERE = Path(__file__).resolve().parent; ROOT = HERE.parents[1]
sys.path.insert(0, str(ROOT / "research" / "w32_asset2"))
import lib as L  # noqa: E402

START, END, IS_END, OOS = "2020-06-01", L.CEND, "2022-12-31", "2023-01-01"
WEIGHTS = [("50", .5), ("60", .6), ("2/3", 2 / 3), ("75", .75), ("100", 1.0)]
MODES = ["A", "B"]
STARTS = ["2020-06-01", "2020-09-01", "2021-01-01", "2021-06-01", "2022-01-01", "2023-01-01"]
OUT = []

def say(*a):
    s = " ".join(str(x) for x in a); OUT.append(s); print(s)

F = {t: L.cfeats(t) for t in ("BTC", "ETH")}
_cache = {}

def sim(t, s, e):
    k = (t, s, e)
    if k not in _cache: _cache[k] = L.csim(F[t], s, e)
    return _cache[k]

def daily(o, s, e):
    idx = pd.date_range(s, e)
    return (o["equity"] / 10000).reindex(idx).ffill().fillna(1.0)

def combine(eb, ee, w, mode):
    """eb, ee: curve normalizzate a 1 alla data d'inizio. Restituisce il conto unico normalizzato a 1."""
    if mode == "A" or w in (0.0, 1.0):
        return w * eb + (1 - w) * ee
    rb, re_ = eb.pct_change().fillna(0), ee.pct_change().fillna(0)
    tot = np.empty(len(eb)); vb, ve = w, 1 - w
    for i, d in enumerate(eb.index):
        if i > 0 and d.month == 1 and d.day == 1:           # ribilancia alla chiusura del 31/12
            v = vb + ve; vb, ve = w * v, (1 - w) * v
        vb *= 1 + rb.iloc[i]; ve *= 1 + re_.iloc[i]; tot[i] = vb + ve
    return pd.Series(tot, index=eb.index)

def metr(tot):
    yrs = (tot.index[-1] - tot.index[0]).days / 365.25; fin = float(tot.iloc[-1])
    dd = float((tot / tot.cummax() - 1).min()); cg = fin ** (1 / yrs) - 1
    ye = tot.groupby(tot.index.year).last(); yb = pd.concat([pd.Series([1.0]), ye.iloc[:-1]]).to_numpy()
    yr = (ye.to_numpy() / yb - 1) * 100
    return dict(fin=round(fin * 10000), cagr=round(cg * 100, 1), dd=round(dd * 100, 1), cd_raw=cg / abs(dd),
                cd=round(cg / abs(dd), 2), anno_peggiore=f"{ye.index[int(yr.argmin())]} {yr.min():+.1f}%")

def drop_best(o, eq):
    """Toglie il trade migliore (P&L, aperta inclusa) azzerando i rendimenti giornalieri del conto fra entrata e uscita."""
    tr = L.otrades(o)
    if not tr: return eq
    b = max(tr, key=lambda t: t["pnl"]); r = eq.pct_change().fillna(0)
    a = pd.Timestamp(b["entry"]); z = pd.Timestamp(b["exit"]) if b.get("exit") else eq.index[-1]
    r[(r.index >= a) & (r.index <= z)] = 0.0
    return (1 + r).cumprod() * float(eq.iloc[0]), b

def grid(s, e, tag, rows):
    ob, oe = sim("BTC", s, e), sim("ETH", s, e); eb, ee = daily(ob, s, e), daily(oe, s, e); res = {}
    for wn, w in WEIGHTS:
        for m in MODES:
            r = metr(combine(eb, ee, w, m)); res[(wn, m)] = r
            rows.append(dict(periodo=tag, inizio=s, fine=e, peso_btc=wn, modo=m, **{k: v for k, v in r.items() if k != "cd_raw"}))
    return res, (ob, oe, eb, ee)

if __name__ == "__main__":
    rows = []
    # ---------------------------------------------------------------- controlli
    say("== Controlli ==")
    ref = pd.read_csv(L.HERE / "trades_crypto.csv")
    for t in ("BTC", "ETH"):
        o = sim(t, START, END); m = L.omet(o); tr = L.otrades(o); rr = ref[ref.ticker == t]
        same = len(rr) == len(tr) and all(str(a["entry"])[:10] == b.entry and abs(a["pnl"] - (b.pnl if pd.notna(b.pnl) else b.pnl_close)) < 1e-9
                                          for a, b in zip(tr, rr.itertuples()))
        say(f"{t} dal {START}: finale {m['fin']:,} $, DD {m['dd']}%, trade {len(tr)}; trade identici a w32_asset2/trades_crypto.csv: {same}")
    eb0, ee0 = daily(sim("BTC", START, END), START, END), daily(sim("ETH", START, END), START, END)
    m50 = metr(combine(eb0, ee0, .5, "A")); mq6, _ = L.port([sim("BTC", START, END)["equity"], sim("ETH", START, END)["equity"]], START)
    say(f"50/50 A dal {START}: finale {m50['fin']:,} $, CAGR/DD {m50['cd']} (w32_asset2 q6: {mq6['fin']:,} $, {mq6['cd']}; atteso 2,44)")
    m23 = metr(combine(eb0, ee0, 2 / 3, "A")); say(f"2/3 A dal {START}: CAGR/DD {m23['cd']} (già visto 2,62)")

    # ---------------------------------------------------------------- griglia IS / OOS / intero
    say("\n== Griglia (finale da 10.000 $, CAGR %, DD %, CAGR/DD, anno peggiore) ==")
    G = {}
    for tag, s, e in (("IS", START, IS_END), ("OOS", OOS, END), ("intero", START, END)):
        G[tag], _ = grid(s, e, tag, rows)
        say(f"-- {tag} {s} → {e}")
        for (wn, m), r in G[tag].items():
            say(f"  BTC {wn:>3} {m}: {r['fin']:>8,} $ · CAGR {r['cagr']:5.1f} · DD {r['dd']:6.1f} · C/DD {r['cd']:.2f} ({r['cd_raw']:.4f}) · peggiore {r['anno_peggiore']}")

    # ---------------------------------------------------------------- scelta IS
    adm = {k: v for k, v in G["IS"].items() if v["dd"] >= -30}
    ch = max(adm, key=lambda k: adm[k]["cd_raw"]); say(f"\n== Scelta IS ==\nammissibili (DD ≥ −30%): {len(adm)}/10; scelta: BTC {ch[0]}% modo {ch[1]} "
                                                       f"(CAGR/DD IS {adm[ch]['cd_raw']:.4f})")
    rk = sorted(adm, key=lambda k: -adm[k]["cd_raw"]); say("ordine IS: " + " > ".join(f"{a}{b} {adm[(a, b)]['cd_raw']:.3f}" for a, b in rk))
    wch = dict(WEIGHTS)[ch[0]]; base = ("50", "A")

    # ---------------------------------------------------------------- criteri OOS
    say("\n== Giudizio OOS 2023-01 → oggi ==")
    c = G["OOS"][ch]; b = G["OOS"][base]
    c1 = c["cd_raw"] > b["cd_raw"]; say(f"(1) CAGR/DD scelta {c['cd_raw']:.3f} vs 50/50 A {b['cd_raw']:.3f} → {c1}")
    ob, oe = sim("BTC", OOS, END), sim("ETH", OOS, END); eb, ee = daily(ob, OOS, END), daily(oe, OOS, END)
    ebx, bb = drop_best(ob, eb); eex, be = drop_best(oe, ee)
    cx, bx = metr(combine(ebx, eex, wch, ch[1])), metr(combine(ebx, eex, .5, "A"))
    c2 = cx["cd_raw"] > bx["cd_raw"]
    say(f"(2) senza il migliore di BTC ({bb['entry']} {bb['side']} {bb['pnl'] * 100:+.1f}%) e di ETH ({be['entry']} {be['side']} {be['pnl'] * 100:+.1f}%): "
        f"scelta {cx['fin']:,} $ DD {cx['dd']} C/DD {cx['cd_raw']:.3f} vs 50/50 A {bx['fin']:,} $ DD {bx['dd']} C/DD {bx['cd_raw']:.3f} → {c2}")
    rows += [dict(periodo="OOS senza migliori", inizio=OOS, fine=END, peso_btc=k[0], modo=k[1], **{q: v for q, v in r.items() if q != "cd_raw"})
             for k, r in ((ch, cx), (base, bx))]
    wins = 0; say("(3) date di partenza (fino a oggi), CAGR/DD scelta vs 50/50 A:")
    SD = {}
    for s in STARTS:
        res, _ = grid(s, END, f"da {s}", rows); SD[s] = res
        ok = res[ch]["cd_raw"] > res[base]["cd_raw"]; wins += ok
        say(f"    {s}: {res[ch]['cd']:.2f} (DD {res[ch]['dd']}) vs {res[base]['cd']:.2f} (DD {res[base]['dd']}) → {ok}")
    c3 = wins >= 4; say(f"    vince in {wins}/6 → {c3}")
    c4 = c["dd"] >= b["dd"] - 3; say(f"(4) DD OOS scelta {c['dd']} vs 50/50 A {b['dd']} (tolleranza 3 punti) → {c4}")
    passa = c1 and c2 and c3 and c4
    say(f"ESITO: {'PROPORRE il cambio a BTC ' + ch[0] + '% modo ' + ch[1] if passa else 'il 50/50 RESTA'}"
        if ch != base else "ESITO: la scelta IS è già il 50/50 A: il 50/50 RESTA")

    # ---------------------------------------------------------------- descrittivo: gli stessi 4 criteri per gli altri pesi (non preregistrato)
    say("\n== Descrittivo (non preregistrato) · i 4 criteri OOS per ogni peso in modo A ==")
    for wn, w in WEIGHTS[1:]:
        k = (wn, "A"); a1 = G["OOS"][k]["cd_raw"] > b["cd_raw"]
        a2x = metr(combine(ebx, eex, w, "A")); a2 = a2x["cd_raw"] > bx["cd_raw"]
        a3 = sum(SD[s][k]["cd_raw"] > SD[s][base]["cd_raw"] for s in STARTS); a4 = G["OOS"][k]["dd"] >= b["dd"] - 3
        say(f"  BTC {wn:>3} A: (1) {G['OOS'][k]['cd']:.2f} {a1} · (2) {a2x['cd']:.2f} vs {bx['cd']:.2f} {a2} · (3) {a3}/6 · "
            f"(4) DD {G['OOS'][k]['dd']} {a4} · su 60.000 $: {w * 60000:,.0f} BTC + {(1 - w) * 60000:,.0f} ETH, DD OOS ≈ {G['OOS'][k]['dd'] / 100 * 60000:,.0f} $")
    say(f"  BTC  50 A: su 60.000 $: 30,000 BTC + 30,000 ETH, DD OOS ≈ {b['dd'] / 100 * 60000:,.0f} $")

    # ---------------------------------------------------------------- descrittivo: anni e contributo al DD
    say("\n== Descrittivo · rendimenti annui dei due conti (dal 2020-06, ognuno da 10.000 $) ==")
    for t, e_ in (("BTC", eb0), ("ETH", ee0)):
        ye = e_.groupby(e_.index.year).last(); yb = pd.concat([pd.Series([1.0]), ye.iloc[:-1]]).to_numpy()
        say(f"  {t}: " + " · ".join(f"{y} {v:+.0f}%" for y, v in zip(ye.index, (ye.to_numpy() / yb - 1) * 100)))
    for wn, w in (("50", .5), ("2/3", 2 / 3), ("100", 1.0)):
        tot = combine(eb0, ee0, w, "A"); ye = tot.groupby(tot.index.year).last(); yb = pd.concat([pd.Series([1.0]), ye.iloc[:-1]]).to_numpy()
        say(f"  conto BTC {wn} A: " + " · ".join(f"{y} {v:+.0f}%" for y, v in zip(ye.index, (ye.to_numpy() / yb - 1) * 100)))
    say("  DD massimo per anno del conto unico (A), BTC 50 / 2/3 / 100:")
    for y in range(2020, 2027):
        vals = []
        for w in (.5, 2 / 3, 1.0):
            t_ = combine(eb0, ee0, w, "A"); t_ = t_[t_.index.year == y]; vals.append((t_ / t_.cummax() - 1).min() * 100)
        say(f"    {y}: " + " / ".join(f"{v:.1f}" for v in vals))
    for wn, w in (("50", .5), ("2/3", 2 / 3)):
        tot = combine(eb0, ee0, w, "A"); dd = tot / tot.cummax() - 1; tr = dd.idxmin(); pk = tot[:tr].idxmax()
        db = (w * (eb0[tr] - eb0[pk])) / tot[pk] * 100; de = ((1 - w) * (ee0[tr] - ee0[pk])) / tot[pk] * 100
        sh = w * eb0[pk] / tot[pk] * 100
        say(f"  DD massimo BTC {wn} A: {pk.date()} → {tr.date()} {dd.min() * 100:.1f}% = BTC {db:+.1f} punti + ETH {de:+.1f} punti "
            f"(quota BTC al picco {sh:.0f}%)")
    corr = eb0.resample("W-SUN").last().pct_change().corr(ee0.resample("W-SUN").last().pct_change())
    say(f"  correlazione dei rendimenti settimanali BTC/ETH (conti W3.2, dal 2020-06): {corr:.2f}")

    # ---------------------------------------------------------------- ricampionamento a blocchi
    say("\n== Ricampionamento a blocchi (5.000 estrazioni, blocchi di 13 settimane, 156 settimane, seme 7) ==")
    wb_ = eb0.resample("W-SUN").last().pct_change().dropna().to_numpy(); we_ = ee0.resample("W-SUN").last().pct_change().dropna().to_numpy()
    n = len(wb_); rng = np.random.default_rng(7); H, B = 156, 13; nb = H // B
    def cdw(rb, re_, w, mode):
        vb, ve, tot = w, 1 - w, np.empty(len(rb))
        for i in range(len(rb)):
            if mode == "B" and i > 0 and i % 52 == 0:
                v = vb + ve; vb, ve = w * v, (1 - w) * v
            vb *= 1 + rb[i]; ve *= 1 + re_[i]; tot[i] = vb + ve
        eq = np.r_[1.0, tot]; dd = abs((eq / np.maximum.accumulate(eq) - 1).min()); cg = eq[-1] ** (1 / 3) - 1
        return (cg / dd if dd > 0 else np.inf), eq[-1], dd
    win_cd = win_fin = win_dd = 0; diffs = []
    for _ in range(5000):
        st = rng.integers(0, n - B + 1, nb); ix = np.concatenate([np.arange(s0, s0 + B) for s0 in st])
        a = cdw(wb_[ix], we_[ix], wch, ch[1]); z = cdw(wb_[ix], we_[ix], .5, "A")
        win_cd += a[0] > z[0]; win_fin += a[1] > z[1]; win_dd += a[2] < z[2]; diffs.append(a[0] - z[0])
    diffs = np.array(diffs[:]); diffs = diffs[np.isfinite(diffs)]
    say(f"  scelta BTC {ch[0]} {ch[1]} contro 50/50 A su 3 anni: P(CAGR/DD più alto) {win_cd / 5000:.1%} · P(finale più alto) {win_fin / 5000:.1%} · "
        f"P(DD più piccolo) {win_dd / 5000:.1%} · differenza CAGR/DD mediana {np.median(diffs):+.2f} (5°–95° {np.percentile(diffs, 5):+.2f} / {np.percentile(diffs, 95):+.2f})")
    if ch[0] != "2/3":
        win = 0
        rng = np.random.default_rng(7)
        for _ in range(5000):
            st = rng.integers(0, n - B + 1, nb); ix = np.concatenate([np.arange(s0, s0 + B) for s0 in st])
            win += cdw(wb_[ix], we_[ix], 2 / 3, "A")[0] > cdw(wb_[ix], we_[ix], .5, "A")[0]
        say(f"  (riferimento) BTC 2/3 A contro 50/50 A: P(CAGR/DD più alto) {win / 5000:.1%}")

    pd.DataFrame(rows).to_csv(HERE / "risultati.csv", index=False)
    (HERE / "out.txt").write_text("\n".join(OUT) + "\n")
