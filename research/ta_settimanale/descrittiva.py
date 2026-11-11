"""Parte 1 · descrittiva: MA 200 giorni × MACD settimanale. Uso: python3 descrittiva.py → descrittiva.txt + desc_*.csv"""
import numpy as np
import pandas as pd
import lib

OUT = []
rng = np.random.default_rng(7)


def log(s=""):
    print(s)
    OUT.append(str(s))


f, fl = lib.load()
w, d, mo = lib.indicators(fl)
w = w[w.index >= "2012-07-01"].copy()
c = w["wclose"]
for k in (4, 12, 26):
    w[f"f{k}"] = c.shift(-k) / c - 1
PER = {"tutto": (None, None), "pre-2021": (None, "2020-12-31"), "dal 2021": ("2021-01-01", None)}
log(f"Settimane {w.index[0].date()} → {w.index[-1].date()} (n={len(w)}); media 200 settimane valida dal {w['sma200w'].first_valid_index().date()}")

# ---- 1. accordo
log("\n== 1. Accordo fra prezzo vs MA200g e MACD settimanale (% settimane concordi · phi)")
rows = []
for ma in ("sma200", "ema200"):
    A = w["wclose"] > w[ma]
    for tag, nm in (("", "12/26/9"), ("f", "8/21/5")):
        for kind, B in (("segnale", w[f"macd{tag}"] > w[f"sig{tag}"]), ("zero", w[f"macd{tag}"] > 0)):
            r = dict(ma=ma, macd=nm, confronto=kind)
            for pn, (a, b) in PER.items():
                m = pd.Series(True, w.index) & (w.index >= (a or "1900")) & (w.index <= (b or "2100"))
                r[f"concordi_{pn}"] = round(float((A[m] == B[m]).mean() * 100), 1)
                r[f"phi_{pn}"] = round(float(np.corrcoef(A[m].astype(float), B[m].astype(float))[0, 1]), 2)
            rows.append(r)
t = pd.DataFrame(rows)
t.to_csv(lib.HERE / "desc_accordo.csv", index=False)
log(t.to_string(index=False))
dist = w["wclose"] / w["sma200"] - 1
for tag, nm in (("", "12/26/9"), ("f", "8/21/5")):
    mn = w[f"macd{tag}"] / w["wclose"]
    hn = (w[f"macd{tag}"] - w[f"sig{tag}"]) / w["wclose"]
    log(f"corr(distanza da SMA200g, MACD {nm}/prezzo) = {dist.corr(mn):.2f} (Spearman {dist.corr(mn, method='spearman'):.2f}); "
        f"con l'istogramma/prezzo = {dist.corr(hn):.2f}; variazioni a 4 sett.: {dist.diff(4).corr(mn.diff(4)):.2f}")
log("Stato attuale: " + ", ".join(f"{k}={w[k].iloc[-1]:.2f}" for k in ("wclose", "sma200", "ema200", "mayer", "macd", "sig", "macdf", "sigf", "sma200w")))

# ---- 2. anticipo/ritardo alle svolte
log("\n== 2. Svolte (zigzag chiusure settimanali: massimo = poi −30%, minimo = poi +50%)")
cv = c.to_numpy()
piv, mode, ext = [], "up", 0
for i in range(1, len(cv)):
    if mode == "up":
        if cv[i] > cv[ext]:
            ext = i
        elif cv[i] <= 0.7 * cv[ext]:
            piv.append(("top", ext)); mode, ext = "dn", i
    else:
        if cv[i] < cv[ext]:
            ext = i
        elif cv[i] >= 1.5 * cv[ext]:
            piv.append(("bot", ext)); mode, ext = "up", i
IND = {"MACD12/26/9 vs segnale": w["macd"] > w["sig"], "MACD8/21/5 vs segnale": w["macdf"] > w["sigf"],
       "MACD12/26/9 vs zero": w["macd"] > 0, "prezzo vs EMA200g": c > w["ema200"], "prezzo vs SMA200g": c > w["sma200"],
       "pendenza SMA200g (28g)": w["slope28"] > 0, "incrocio 50/200g": w["gc"].astype(bool)}
rows = []
for kind, i in piv:
    r = dict(tipo=kind, data=str(w.index[i].date()), prezzo=round(cv[i]))
    for nm, bull in IND.items():
        b = bull.to_numpy()
        want = (kind == "bot")       # dopo un minimo serve lo stato rialzista, dopo un massimo quello ribassista
        if b[i] == want:
            j = i
            while j > 0 and b[j - 1] == want:
                j -= 1
            lag, px = j - i, cv[j]
        else:
            j = i
            while j < len(b) and b[j] != want:
                j += 1
            lag, px = (j - i, cv[j]) if j < len(b) else (np.nan, np.nan)
        r[nm + " · sett"] = lag
        r[nm + " · prezzo%"] = round((px / cv[i] - 1) * 100, 1) if px == px else np.nan
    rows.append(r)
sv = pd.DataFrame(rows)
sv.to_csv(lib.HERE / "desc_svolte.csv", index=False)
log(f"Svolte trovate: {sum(sv.tipo == 'top')} massimi, {sum(sv.tipo == 'bot')} minimi")
log(sv[["tipo", "data", "prezzo"]].to_string(index=False))
log("\nMediana delle settimane dal massimo/minimo al cambio di stato (negativo = già girato prima) e prezzo a quel punto rispetto alla svolta")
med = []
for nm in IND:
    r = dict(indicatore=nm)
    for kind, lab in (("top", "massimi"), ("bot", "minimi")):
        s = sv[sv.tipo == kind]
        r[f"{lab}: sett. (mediana)"] = s[nm + " · sett"].median()
        r[f"{lab}: min/max sett."] = f"{s[nm + ' · sett'].min():.0f}/{s[nm + ' · sett'].max():.0f}"
        r[f"{lab}: prezzo% (mediana)"] = s[nm + " · prezzo%"].median()
    med.append(r)
med = pd.DataFrame(med)
med.to_csv(lib.HERE / "desc_svolte_mediane.csv", index=False)
log(med.to_string(index=False))
# chi gira prima: MACD-segnale contro prezzo-SMA200
for kind in ("top", "bot"):
    s = sv[sv.tipo == kind]
    dlt = s["prezzo vs SMA200g · sett"] - s["MACD12/26/9 vs segnale · sett"]
    log(f"{kind}: il MACD (segnale) gira prima della SMA200g in {int((dlt > 0).sum())}/{len(s)} svolte, anticipo mediano {dlt.median():.0f} settimane")


# ---- 3. rendimenti futuri per stato
def perm_p(x, state, nrep=2000):
    """p a due code: media(x | stato) − media(x) contro slittamenti circolari dello stato."""
    ok = ~np.isnan(x)
    x, s = x[ok], state[ok]
    if s.sum() < 5:
        return np.nan
    obs = x[s].mean() - x.mean()
    n = len(x)
    ks = rng.integers(26, n - 26, nrep)
    sim = np.array([x[np.roll(s, k)].mean() - x.mean() for k in ks])
    return float((np.abs(sim) >= abs(obs)).mean())


def table(states: dict, title: str, fn: str):
    log(f"\n== {title}")
    rows = []
    for pn, (a, b) in PER.items():
        m = (w.index >= (a or "1900")) & (w.index <= (b or "2100"))
        ww = w[m]
        for nm, st in states.items():
            s = st[m].fillna(False).to_numpy(bool)
            r = dict(periodo=pn, stato=nm, n=int(s.sum()), quota=round(s.mean() * 100))
            for k in (4, 12, 26):
                x = ww[f"f{k}"].to_numpy(float)
                xs = x[s & ~np.isnan(x)]
                if len(xs) < 5:
                    r.update({f"media{k}": np.nan, f"mediana{k}": np.nan, f"pos{k}": np.nan, f"p{k}": np.nan})
                    continue
                r.update({f"media{k}": round(xs.mean() * 100, 1), f"mediana{k}": round(np.median(xs) * 100, 1),
                          f"pos{k}": round((xs > 0).mean() * 100), f"p{k}": round(perm_p(x, s), 3)})
            rows.append(r)
        r = dict(periodo=pn, stato="(tutte le settimane)", n=len(ww), quota=100)
        for k in (4, 12, 26):
            x = ww[f"f{k}"].dropna()
            r.update({f"media{k}": round(x.mean() * 100, 1), f"mediana{k}": round(x.median() * 100, 1), f"pos{k}": round((x > 0).mean() * 100), f"p{k}": np.nan})
        rows.append(r)
    t = pd.DataFrame(rows)
    t.to_csv(lib.HERE / fn, index=False)
    log(t.to_string(index=False))
    return t


up, ms, mz = c > w["sma200"], w["macd"] > w["sig"], w["macd"] > 0
table({"sopra SMA200 · MACD>segnale": up & ms, "sopra SMA200 · MACD<segnale": up & ~ms,
       "sotto SMA200 · MACD>segnale": ~up & ms, "sotto SMA200 · MACD<segnale": ~up & ~ms},
      "3a. Rendimenti futuri a 4/12/26 settimane · SMA200g × MACD 12/26/9 vs segnale", "desc_stati_segnale.csv")
table({"sopra SMA200 · MACD>0": up & mz, "sopra SMA200 · MACD<0": up & ~mz,
       "sotto SMA200 · MACD>0": ~up & mz, "sotto SMA200 · MACD<0": ~up & ~mz},
      "3b. SMA200g × MACD 12/26/9 vs zero", "desc_stati_zero.csv")
upe, msf = c > w["ema200"], w["macdf"] > w["sigf"]
table({"sopra EMA200 · MACD8>segnale": upe & msf, "sopra EMA200 · MACD8<segnale": upe & ~msf,
       "sotto EMA200 · MACD8>segnale": ~upe & msf, "sotto EMA200 · MACD8<segnale": ~upe & ~msf},
      "3c. EMA200g × MACD 8/21/5 vs segnale", "desc_stati_ema_8215.csv")
table({"solo: sopra SMA200": up, "solo: sotto SMA200": ~up, "solo: MACD>segnale": ms, "solo: MACD<segnale": ~ms,
       "solo: MACD>0": mz, "solo: MACD<0": ~mz}, "3d. Le due variabili prese da sole", "desc_stati_singoli.csv")
sl = w["slope28"] > 0
table({"SMA200 in salita": sl, "SMA200 in discesa": ~sl, "salita · prezzo sopra": sl & up, "salita · prezzo sotto": sl & ~up,
       "discesa · prezzo sopra": ~sl & up, "discesa · prezzo sotto": ~sl & ~up},
      "4a. Pendenza della SMA200g (28 giorni) come regime", "desc_pendenza.csv")
my = w["mayer"]
table({"Mayer < 0,8": my < 0.8, "Mayer 0,8–1": (my >= 0.8) & (my < 1), "Mayer 1–1,5": (my >= 1) & (my < 1.5),
       "Mayer 1,5–2,4": (my >= 1.5) & (my <= 2.4), "Mayer > 2,4": my > 2.4},
      "4b. Fasce del Mayer multiple (chiusura / SMA200g)", "desc_mayer.csv")
b200 = (c < w["sma200w"]) & w["sma200w"].notna()
a200 = (c >= w["sma200w"]) & w["sma200w"].notna()
table({"sotto la media 200 settimane": b200, "sopra la media 200 settimane": a200}, "4c. Media a 200 SETTIMANE (dal 2015-06)", "desc_200w.csv")
for nm, s in (("Mayer > 2,4", my > 2.4), ("Mayer < 0,8", my < 0.8), ("sotto 200 settimane", b200)):
    ep = (s & ~s.shift(1, fill_value=False))
    log(f"episodi distinti '{nm}': {int(ep.sum())} → inizi: {', '.join(str(x.date()) for x in w.index[ep])}")

# ---- golden / death cross (giornaliero)
log("\n== 4d. Golden / death cross SMA50g × SMA200g (eventi giornalieri dal 2012)")
dd = d[d.index >= "2012-07-01"]
g = dd["gc"].astype(bool)
ev = g != g.shift(1)
ev.iloc[0] = False
rows = []
dates = list(dd.index[ev])
for i, t0 in enumerate(dates):
    kind = "golden" if g.loc[t0] else "death"
    px = dd["close"].loc[t0]
    r = dict(tipo=kind, data=str(t0.date()), prezzo=round(px))
    for k in (28, 84, 182):
        j = dd.index.searchsorted(t0) + k
        r[f"r{k}g"] = round((dd["close"].iloc[j] / px - 1) * 100, 1) if j < len(dd) else np.nan
    nxt = dates[i + 1] if i + 1 < len(dates) else dd.index[-1]
    r["fino_all_opposto%"] = round((dd["close"].loc[nxt] / px - 1) * 100, 1)
    r["giorni"] = (nxt - t0).days
    seg = dd["close"].loc[t0:nxt]
    r["dal_massimo%" if kind == "death" else "dal_minimo%"] = round((px / (dd["close"].loc[:t0].iloc[-365:].max() if kind == "death" else dd["close"].loc[:t0].iloc[-365:].min()) - 1) * 100, 1)
    rows.append(r)
gx = pd.DataFrame(rows)
gx.to_csv(lib.HERE / "desc_cross.csv", index=False)
log(gx.to_string(index=False))
for kind in ("golden", "death"):
    s = gx[gx.tipo == kind]
    log(f"{kind}: n={len(s)} · mediana 28g {s.r28g.median():+.1f}% · 84g {s.r84g.median():+.1f}% · 182g {s.r182g.median():+.1f}% · "
        f"positivi a 182g {int((s.r182g > 0).sum())}/{int(s.r182g.notna().sum())} · fino all'incrocio opposto: mediana {s['fino_all_opposto%'].median():+.1f}%, "
        f"positivi {int((s['fino_all_opposto%'] > 0).sum())}/{len(s)}")
alld = dd["close"]
log("riferimento (tutti i giorni): mediana 28g {:+.1f}% · 84g {:+.1f}% · 182g {:+.1f}%".format(
    *[float((alld.shift(-k) / alld - 1).median() * 100) for k in (28, 84, 182)]))
(lib.HERE / "descrittiva.txt").write_text("\n".join(OUT))
