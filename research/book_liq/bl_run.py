"""Studio book_liq (PREREG.md): H1 squilibrio, H2 muri, H3 confluenza, H4 descrittivo. Output in research/book_liq/.
Uso: BL_WORK=<cache> python research/book_liq/bl_run.py
"""
from __future__ import annotations

import math
import sys
from pathlib import Path

import numpy as np
import pandas as pd
from scipy import stats

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import bl_data as D  # noqa: E402

RNG = np.random.default_rng(20261122)
OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s); OUT.append(s)


def wilson(k, n, z=1.96):
    if n == 0:
        return (np.nan, np.nan)
    p = k / n; d = 1 + z * z / n
    c = (p + z * z / (2 * n)) / d; h = z * math.sqrt(p * (1 - p) / n + z * z / (4 * n * n)) / d
    return (c - h, c + h)


# ------------------------------------------------------------------ dati
ob = pd.read_csv(D.DATA / "orderbook.csv", parse_dates=["ts"])
m1 = D.m1()
close = m1["close"]
ob["t0"] = ob["ts"].dt.floor("min")
ob["p0"] = close.reindex(ob["t0"]).to_numpy()
for h in (1, 4, 24):
    ob[f"r{h}"] = close.reindex(ob["t0"] + pd.Timedelta(hours=h)).to_numpy() / ob["p0"] - 1
ob["rpast24"] = ob["p0"] / close.reindex(ob["t0"] - pd.Timedelta(hours=24)).to_numpy() - 1
ob["day"] = ob["ts"].dt.normalize()
ob["half"] = np.where(ob["ts"] < "2026-11-16", "07-15/11", "16-22/11")
ob["wall_ratio"] = ob["wall_ask_usd"] / ob["wall_bid_usd"]
say(f"Book: {ob.ts.min()} → {ob.ts.max()}, {len(ob)} foto, {ob.day.nunique()} giorni; candele 1m fino a {m1.index.max()}")
say(f"Foto con esito a 1h/4h/24h: {ob.r1.notna().sum()}/{ob.r4.notna().sum()}/{ob.r24.notna().sum()}")

# ------------------------------------------------------------------ H1
say("\n== H1 squilibrio (bid−ask)/(bid+ask) → rendimento futuro ==")
rows = []


def h1_cell(x: pd.Series, y: pd.Series, days: pd.Series, half: pd.Series, name: str, hz: int):
    k = x.notna() & y.notna()
    x, y, days, half = x[k].to_numpy(), y[k].to_numpy(), days[k].to_numpy(), half[k].to_numpy()
    n = len(x)
    rho = stats.spearmanr(x, y).statistic
    # permutazione a blocchi: spostamento circolare dei rendimenti di almeno 24 foto
    sh = RNG.integers(24, n - 24, 2000)
    perm = np.array([stats.spearmanr(x, np.roll(y, s)).statistic for s in sh])
    p = float((np.abs(perm) >= abs(rho)).mean())
    # bootstrap per giorni
    ud = np.unique(days); idx = {d: np.where(days == d)[0] for d in ud}
    bs = []
    for _ in range(1000):
        sel = np.concatenate([idx[d] for d in RNG.choice(ud, len(ud))])
        if len(np.unique(x[sel])) > 3:
            bs.append(stats.spearmanr(x[sel], y[sel]).statistic)
    lo, hi = np.nanpercentile(bs, [2.5, 97.5])
    q = pd.qcut(pd.Series(x).rank(method="first"), 5, labels=False)
    qm = pd.Series(y).groupby(q).mean() * 100
    qn = pd.Series(y).groupby(q).size()
    hs = {hv: stats.spearmanr(x[half == hv], y[half == hv]).statistic for hv in ("07-15/11", "16-22/11")}
    neff = len(ud) * 24 / hz if hz < 24 else len(ud)
    r = {"segnale": name, "orizzonte_h": hz, "n_foto": n, "n_indip_circa": int(min(n, neff)), "rho": round(rho, 3),
         "ic95_lo": round(lo, 3), "ic95_hi": round(hi, 3), "p_blocchi": round(p, 3),
         "rho_07_15": round(hs["07-15/11"], 3), "rho_16_22": round(hs["16-22/11"], 3),
         **{f"Q{i+1}_%": round(qm.iloc[i], 3) for i in range(5)}, "n_per_Q": int(qn.min()),
         "Q5_Q1_%": round(qm.iloc[4] - qm.iloc[0], 3)}
    r["indizio"] = bool(abs(rho) >= 0.10 and p < 0.05 and np.sign(hs["07-15/11"]) == np.sign(hs["16-22/11"]) == np.sign(rho)
                        and abs(r["Q5_Q1_%"]) > 0.30)
    rows.append(r)
    say(f"{name:14s} {hz:>2}h n={n:3d} (indip.~{r['n_indip_circa']}) ρ={rho:+.3f} IC95 [{lo:+.2f},{hi:+.2f}] p_blocchi={p:.3f} "
        f"metà {hs['07-15/11']:+.2f}/{hs['16-22/11']:+.2f} Q1..Q5 % " + " ".join(f"{v:+.2f}" for v in qm) +
        f" Q5−Q1 {r['Q5_Q1_%']:+.2f} → {'INDIZIO' if r['indizio'] else 'no'}")


for col, name in (("imb_1", "imb ±1%"), ("imb_2", "imb ±2%")):
    for hz in (1, 4, 24):
        h1_cell(ob[col], ob[f"r{hz}"], ob["day"], ob["half"], name, hz)
say("-- non preregistrato, descrittivo (idea dello screenshot): rapporto muro ask / muro bid, e fasce strette")
for col, name in (("wall_ratio", "muro ask/bid"), ("imb_0.25", "imb ±0,25%"), ("imb_0.5", "imb ±0,5%")):
    for hz in (1, 4, 24):
        h1_cell(ob[col], ob[f"r{hz}"], ob["day"], ob["half"], name, hz)
pd.DataFrame(rows).to_csv(HERE / "h1_squilibrio.csv", index=False)
for col in ("imb_1", "imb_2", "wall_ratio"):
    k = ob[col].notna() & ob["rpast24"].notna()
    say(f"controllo momentum: ρ({col}, rendimento 24h PRECEDENTI) = {stats.spearmanr(ob.loc[k, col], ob.loc[k, 'rpast24']).statistic:+.3f} (n {k.sum()})")
say(f"rapporto muro ask/bid aggregato (5 exchange): mediana {ob.wall_ratio.median():.2f}, max {ob.wall_ratio.max():.2f}, "
    f"foto con ask ≥ 3× bid: {(ob.wall_ratio >= 3).sum()}, ≥ 2×: {(ob.wall_ratio >= 2).sum()}; bid ≥ 2× ask: {(ob.wall_ratio <= 0.5).sum()}")

# ------------------------------------------------------------------ H2 / H3 esiti
HOR = pd.Timedelta(hours=24)
hi_, lo_ = m1["high"], m1["low"]


def outcome(t0: pd.Timestamp, level: float, side: str) -> dict | None:
    """side 'bid' = livello sotto (supporto), 'ask' = sopra. Esiti entro 24 ore sulle candele 1m dopo la foto."""
    a = t0 + pd.Timedelta(minutes=1)
    if a + HOR > m1.index[-1]:
        return None
    H, L = hi_[a:a + HOR].to_numpy(), lo_[a:a + HOR].to_numpy()
    if side == "bid":
        touch = np.where(L <= level)[0]; beyond = np.where(L <= level * 0.997)[0]
        reach = len(touch) > 0
        sup = len(beyond) > 0
        reb = False
        if reach:
            i = touch[0]; up = np.where(H[i:] >= level * 1.01)[0]; br = np.where(L[i:] <= level * 0.997)[0]
            reb = len(up) > 0 and (len(br) == 0 or up[0] < br[0])
    else:
        touch = np.where(H >= level)[0]; beyond = np.where(H >= level * 1.003)[0]
        reach = len(touch) > 0
        sup = len(beyond) > 0
        reb = False
        if reach:
            i = touch[0]; dn = np.where(L[i:] <= level * 0.99)[0]; br = np.where(H[i:] >= level * 1.003)[0]
            reb = len(dn) > 0 and (len(br) == 0 or dn[0] < br[0])
    return {"raggiunto": reach, "superato": sup, "rimbalzo": reb}


def episodes(R: float, dmin: float) -> pd.DataFrame:
    ev = []
    for s in ("bid", "ask"):
        r = ob[f"wall_{s}_usd"] / (ob[f"{s}_1"] / 20); dist = ob[f"wall_{s}_dist"].abs()
        e = ob[(r >= R) & (dist >= dmin)]
        last = None
        for i, x in e.iterrows():
            new = last is None or (x.ts - last[0]) > pd.Timedelta(hours=6) or abs(x[f"wall_{s}_px"] / last[1] - 1) > 0.0025
            last = (x.ts, x[f"wall_{s}_px"])
            if new:
                # livello riferito al prezzo 1m della foto (stessa distanza del muro dal mid)
                d = x[f"wall_{s}_dist"] / 100
                ev.append({"i": i, "ts": x.ts, "t0": x.t0, "lato": s, "p0": x.p0, "dist": d, "livello": x.p0 * (1 + d),
                           "muro_usd": x[f"wall_{s}_usd"], "R": round(r[i], 2)})
    return pd.DataFrame(ev)


# base casuale: tutte le foto con 24 ore di esito, per ogni distanza richiesta
base_idx = [i for i, x in ob.iterrows() if x.t0 + pd.Timedelta(minutes=1) + HOR <= m1.index[-1]]
_cache: dict = {}


def base_out(i: int, d: float, side: str) -> dict:
    key = (i, round(d, 5), side)
    if key not in _cache:
        x = ob.loc[i]
        _cache[key] = outcome(x.t0, x.p0 * (1 + d), side)
    return _cache[key]


def test_set(ev: pd.DataFrame, label: str, nperm: int = 3000) -> list[dict]:
    res = []
    if ev.empty:
        say(f"{label}: 0 episodi"); return res
    outs = [outcome(r.t0, r.livello, r.lato) for r in ev.itertuples()]
    keep = [o is not None for o in outs]
    ev = ev[keep].reset_index(drop=True); outs = [o for o in outs if o is not None]
    n = len(ev)
    if n == 0:
        say(f"{label}: 0 episodi con 24h di esito"); return res
    evi = set(ev["i"])
    pool = [i for i in base_idx if i not in evi]
    for m in ("raggiunto", "superato", "rimbalzo"):
        obs = np.mean([o[m] for o in outs])
        # atteso: per ogni episodio, frequenza dell'esito su tutte le altre foto alla stessa distanza e lato
        exp_each = [np.mean([base_out(j, r.dist, r.lato)[m] for j in pool]) for r in ev.itertuples()]
        exp = float(np.mean(exp_each))
        perm = []
        for _ in range(nperm):
            js = RNG.choice(pool, n)
            perm.append(np.mean([base_out(j, r.dist, r.lato)[m] for j, r in zip(js, ev.itertuples())]))
        perm = np.array(perm)
        p = float((np.abs(perm - exp) >= abs(obs - exp) - 1e-12).mean())
        k = int(sum(o[m] for o in outs)); lo, hi = wilson(k, n)
        diff = (obs - exp) * 100
        ind = bool(abs(diff) >= 10 and p < 0.05 and n >= 10)
        res.append({"insieme": label, "esito": m, "n_episodi": n, "k": k, "freq_%": round(obs * 100, 1),
                    "ic95_%": f"{lo*100:.0f}-{hi*100:.0f}", "casuale_%": round(exp * 100, 1), "diff_punti": round(diff, 1),
                    "p_perm": round(p, 3), "indizio": ind})
        say(f"{label:34s} {m:9s} n={n:2d} {k:2d}/{n} = {obs*100:5.1f}% (IC95 {lo*100:.0f}–{hi*100:.0f}) casuale {exp*100:5.1f}% "
            f"diff {diff:+5.1f} p={p:.3f} → {'INDIZIO' if ind else 'no'}")
    return res


say("\n== H2 muro vicino (≥ 3× fascia media ±1%, distanza ≥ 0,3%) → esiti entro 24 ore ==")
h2 = []
ev = episodes(3.0, 0.3)
ev.to_csv(HERE / "h2_episodi.csv", index=False)
say(f"episodi: {len(ev)} (bid {int((ev.lato=='bid').sum())}, ask {int((ev.lato=='ask').sum())}); distanza mediana "
    f"{ev.dist.abs().median()*100:.2f}%")
h2 += test_set(ev, "H2 tutti")
h2 += test_set(ev[ev.lato == "bid"], "H2 muri bid (supporto)")
h2 += test_set(ev[ev.lato == "ask"], "H2 muri ask (resistenza)")
say("-- parametri vicini (trasparenza; da leggere solo se H2 desse un indizio)")
for R, dm in ((2.5, 0.3), (4.0, 0.3), (3.0, 0.2), (3.0, 0.5)):
    h2 += test_set(episodes(R, dm), f"vicini R≥{R} d≥{dm}%", nperm=1000)
pd.DataFrame(h2).to_csv(HERE / "h2_muri.csv", index=False)

# ------------------------------------------------------------------ H3 confluenza
say("\n== H3 confluenza entro 0,5% dal muro ==")
h1h = D.h1()
oc = D.onchain()
sr_cache: dict = {}
conf = []
for r in ev.itertuples():
    lv = r.livello
    mp = D.est_map(h1h, r.ts)
    est = False; est_usd = 0.0
    if mp:
        for c in mp[0] + mp[1]:
            if abs(c["price"] / lv - 1) <= 0.005:
                est = True; est_usd = max(est_usd, c["usd"])
    o = D.onchain_at(oc, r.ts)
    onc = bool(o and any(abs(c["price"] / lv - 1) <= 0.005 for c in o["clusters"]))
    dkey = r.ts.normalize()
    if dkey not in sr_cache:
        sr_cache[dkey] = D.sr_at(r.ts)
    L = sr_cache[dkey]
    srz = next((f"{t}{j+1}" for key, t in (("supports", "S"), ("resistances", "R"))
                for j, z in enumerate(L[key]) if z["lo"] * 0.995 <= lv <= z["hi"] * 1.005), None)
    conf.append({"i": r.i, "ts": r.ts, "lato": r.lato, "livello": round(lv, 0), "dist_%": round(r.dist * 100, 3),
                 "fascia_stimata": est, "fascia_usd": round(est_usd, 0), "onchain": onc, "onchain_disp": o is not None,
                 "sr": srz})
cf = pd.DataFrame(conf)
ev3 = ev.merge(cf[["i", "lato", "fascia_stimata", "onchain", "onchain_disp", "sr"]], on=["i", "lato"])
ev3["qualsiasi"] = ev3["fascia_stimata"] | ev3["onchain"] | ev3["sr"].notna()
ev3.to_csv(HERE / "h3_episodi.csv", index=False)
say(f"episodi H2: {len(ev3)}; con fascia stimata {int(ev3.fascia_stimata.sum())}, on-chain {int(ev3.onchain.sum())} "
    f"(on-chain disponibile in {int(ev3.onchain_disp.sum())}), S/R {int(ev3.sr.notna().sum())}, almeno una {int(ev3.qualsiasi.sum())}")
h3 = []
h3 += test_set(ev3[ev3.fascia_stimata], "H3a muro + fascia stimata")
h3 += test_set(ev3[ev3.onchain], "H3b muro + on-chain")
h3 += test_set(ev3[ev3.sr.notna()], "H3c muro + S/R")
h3 += test_set(ev3[ev3.qualsiasi], "H3 muro + almeno una")
h3 += test_set(ev3[~ev3.qualsiasi], "H3 muro senza confluenza")
pd.DataFrame(h3).to_csv(HERE / "h3_confluenza.csv", index=False)

# ------------------------------------------------------------------ H4 descrittivo
say("\n== H4 descrittivo 13/11–22/11 (short W3.1 dal 16/11 a 65.286) ==")
le = pd.read_csv(D.DATA / "liq_events" / "2026-11.csv"); le["t"] = pd.to_datetime(le["ts"], unit="ms")
liq_day = le.pivot_table(index=le["t"].dt.normalize(), columns="side", values="usd", aggfunc="sum").fillna(0) / 1e6
d1 = m1.resample("D").agg({"open": "first", "high": "max", "low": "min", "close": "last"})
h4 = []
for day in pd.date_range("2026-11-12", "2026-11-22"):
    g = ob[ob.day == day]
    mp = D.est_map(h1h, day + pd.Timedelta(hours=1))
    o = D.onchain_at(oc, day + pd.Timedelta(minutes=59))
    row = {"giorno": day.strftime("%d/%m"), "apertura": round(d1.loc[day, "open"]), "minimo": round(d1.loc[day, "low"]),
           "massimo": round(d1.loc[day, "high"]), "chiusura": round(d1.loc[day, "close"]),
           "foto_book": len(g), "imb1_media": round(g.imb_1.mean(), 3) if len(g) else None,
           "imb2_media": round(g.imb_2.mean(), 3) if len(g) else None,
           "muro_ask/bid_med": round(g.wall_ratio.median(), 2) if len(g) else None,
           "liq_reali_long_M$": round(liq_day.loc[day, "long"], 1) if day in liq_day.index else None,
           "liq_reali_short_M$": round(liq_day.loc[day, "short"], 1) if day in liq_day.index else None,
           "stima_long_sotto5%_M$": round(mp[3] / 1e6, 0) if mp else None, "stima_short_sopra5%_M$": round(mp[4] / 1e6, 0) if mp else None,
           "onchain_long_sotto5%_M$": round(o["long5"] / 1e6, 1) if o else None,
           "onchain_short_sopra5%_M$": round(o["short5"] / 1e6, 1) if o else None,
           "short_W3.1_%": round((65286 / d1.loc[day, "close"] - 1) * 100, 1) if day >= pd.Timestamp("2026-11-16") else None}
    h4.append(row)
h4 = pd.DataFrame(h4)
h4.to_csv(HERE / "h4_giorni.csv", index=False)
say(h4.to_string(index=False))
say("Nota: liquidazioni reali = data/liq_events (OKX, Gate, dYdX, Deribit, Kraken, Lighter; senza Binance e Bybit). "
    "Mappa stimata e on-chain all'01:00 UTC del giorno (dati fino a quell'ora); mappa del 22/11 con OI fino al 21/11 23:00.")

# ------------------------------------------------------------------ contesto e potenza
say("\n== Contesto nella finestra del book ==")
p_a, p_b = close.iloc[close.index.searchsorted(ob.ts.min())], close.iloc[-1]
p16 = 65286
say(f"buy & hold 07/11 → oggi: {p_a:,.0f} → {p_b:,.0f} = {(p_b/p_a-1)*100:+.1f}%; short W3.1 dal 16/11 (65.286, esposizione 0,389): "
    f"movimento {(p16/p_b-1)*100:+.1f}% → sul capitale ~{(p16/p_b-1)*0.389*100:+.1f}% (lordo)")
say("\n== Potenza (α 0,05 bilaterale, potenza 80%) ==")
z = 1.96 + 0.8416
for rho in (0.05, 0.10, 0.20):
    n = (z / math.atanh(rho)) ** 2 + 3
    say(f"ρ = {rho:.2f}: n indipendenti ≈ {n:,.0f} → a 1h ≈ {n/24:,.0f} giorni di foto orarie; a 4h ≈ {n/6:,.0f} giorni; a 24h ≈ {n:,.0f} giorni")
for p0, dd in ((0.5, 0.10), (0.8, 0.10), (0.3, 0.10)):
    n = (1.96 * math.sqrt(p0 * (1 - p0)) + 0.8416 * math.sqrt((p0 + dd) * (1 - p0 - dd))) ** 2 / dd ** 2
    say(f"differenza {dd*100:.0f} punti su base {p0*100:.0f}%: ≈ {n:,.0f} episodi → al ritmo attuale ({len(ev)/15:.1f}/giorno) ≈ {n/(len(ev)/15):,.0f} giorni")

(HERE / "risultati.txt").write_text("\n".join(OUT) + "\n")
