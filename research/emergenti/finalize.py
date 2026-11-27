"""emergenti · universo finale (data/universe.csv): controllo dell'abbinamento per prezzo (build.py -> data/match_raw.csv) e
definizione di "emergente" fissata nel PREREG prima di qualsiasi rendimento:
- emergente_storico (punto nel tempo, senza sopravvivenza): rank 101-200 in almeno una classifica CMC di inizio anno 2021-2025
  (le classifiche storiche ottenibili hanno solo 200 righe); al segnale vale la classifica più recente (counts.py);
- emergente_oggi: rank CoinGecko 101-500 del 27/11/2026 (con bias di sopravvivenza: solo per il periodo in avanti e come vista).
Abbinamento: rapporto prezzo Binance/fonte in [0,5; 2] = ok; fuori = errato (dati tolti); moneta solo storica con dati che
iniziano dopo la sua ultima classifica = non verificato (dati tolti: possibile ticker riusato)."""
import json, re, sys
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; D = HERE / "data"; COINS = D / "coins"
u = pd.read_csv(D / "universe_raw.csv"); u = u[u.escluso.isna()].copy(); m = pd.read_csv(D / "match_raw.csv").set_index("ticker")
s = pd.read_csv(D / "snapshots.csv"); sday = s.groupby("anno").data.first().astype(str).to_dict()
sys.path.insert(0, str(HERE.parent / "w32_asset2" / "crypto")); import universe as U32  # noqa: E402
ssym = {(a, sl): sy for a, sl, sy in zip(s.anno, s.slug, s.simbolo)}
RK = sorted(int(c[5:]) for c in u.columns if re.fullmatch(r"rank_\d{4}", c))
stato, nota = [], []
for r in u.itertuples():
    t = r.ticker; files = list(COINS.glob(f"{t}_*.csv.gz"))
    if not files: stato.append("senza dati"); nota.append(""); continue
    rr = m.loc[t] if t in m.index else pd.Series(dtype=float)
    checks = {k: v for k, v in rr.items() if (k == "oggi_rapporto" or k.startswith("r_")) and v == v and v is not None}
    ch = json.loads(r.chain)
    for k in list(checks):                       # catene riscalate (BTT -> BTTC /1000, NPXS -> PUNDIX x1000): stessa unità
        if k.startswith("r_"):
            sy = ssym.get((int(k[2:]), getattr(r, f"slug_{k[2:]}")), "")
            fac = next((c["fac"] for c in ch if c["base"] == sy), 1)
            checks[k] = round(checks[k] * fac, 3)
    bad = {k: v for k, v in checks.items() if not (0.5 <= v <= 2)}
    first = min(pd.read_csv(p, index_col=0, parse_dates=True, nrows=1).index[0] for p in files if not p.name.endswith("_funding.csv.gz")) if any(not p.name.endswith("_funding.csv.gz") for p in files) else None
    last_snap = max((pd.Timestamp(sday[y]) for y in RK if getattr(r, f"rank_{y}") == getattr(r, f"rank_{y}")), default=None)
    good_hist = any(k.startswith("r_") and k not in bad for k in checks)
    if bad and set(bad) == {"oggi_rapporto"} and good_hist:
        # stesso ticker per due monete: i dati sono della moneta storica (es. ONE = Harmony), il rank di oggi è di un'altra
        st, nt = "verificato (storico)", f"rank di oggi di un'altra moneta con lo stesso ticker ({r.nome}, oggi_rapporto={bad['oggi_rapporto']}): rank_oggi tolto"
        u.loc[r.Index, "rank_oggi"] = np.nan
    elif bad:
        st, nt = "abbinamento errato", "; ".join(f"{k}={v}" for k, v in bad.items())
    elif t in U32.REUSED:
        st, nt = "abbinamento errato", U32.REUSED[t]
    elif not checks and r.rank_oggi != r.rank_oggi and last_snap is not None and first is not None and first > last_snap:
        st, nt = "non verificabile (quotazione Binance successiva)", f"dati dal {first.date()}, ultima classifica {last_snap.date()}"
    else:
        st, nt = ("verificato" if checks else "non verificabile (nessun prezzo di confronto)"), ""
    if st in ("abbinamento errato", "non verificato"):
        for p in files: p.unlink()
    stato.append(st); nota.append(nt)
u["abbinamento"] = stato; u["abbinamento_nota"] = nota
hist = [y for y in RK if 2021 <= y <= 2026]
u["emergente_storico"] = np.any([(u[f"rank_{y}"] > 100) & (u[f"rank_{y}"] <= 200) for y in hist], axis=0)
u["emergente_oggi"] = (u.rank_oggi > 100) & (u.rank_oggi <= 500)
u["top100_oggi"] = u.rank_oggi <= 100
u.to_csv(D / "universe.csv", index=False)
print(u.abbinamento.value_counts().to_string()); print("emergenti storiche", int(u.emergente_storico.sum()), "| oggi", int(u.emergente_oggi.sum()),
      "| unione", int((u.emergente_storico | u.emergente_oggi).sum()))
print(u[u.abbinamento.isin(["abbinamento errato", "non verificato"])][["ticker", "nome", "rank_oggi", "abbinamento_nota"]].to_string())
