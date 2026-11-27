"""emergenti · riepilogo dei conteggi di struttura per DATI.md (nessun rendimento). Scrive data/summary.txt."""
from pathlib import Path
import numpy as np, pandas as pd
HERE = Path(__file__).resolve().parent; D = HERE / "data"
u = pd.read_csv(D / "universe.csv"); c = pd.read_csv(D / "counts_moneta.csv"); s = pd.read_csv(D / "segnali.csv")
raw = pd.read_csv(D / "universe_raw.csv"); L = []
p = lambda *a: L.append(" ".join(str(x) for x in a))  # noqa: E731
p("UNIVERSO"); p("righe grezze", len(raw), "| escluse", int(raw.escluso.notna().sum()), "| incluse", len(u))
p("top 500 di oggi: escluse", int((raw.rank_oggi.notna() & raw.escluso.notna()).sum()), "| incluse", int((raw.rank_oggi.notna() & raw.escluso.isna()).sum()))
p("motivi (oggi):", raw[raw.rank_oggi.notna() & raw.escluso.notna()].escluso.str.split(",").str[0].value_counts().to_dict())
p("abbinamento:", u.abbinamento.value_counts().to_dict())
m = c.merge(u[["ticker", "abbinamento", "bn_perp", "okx_perp_simbolo", "bitget_perp_da", "okx_perp_da", "data_aggiunta_cmc"]], on="ticker", how="left")
for name, sel in (("emergenti storiche (101-200 in una classifica 2021-2026)", m.emergente_storico == True),
                  ("emergenti oggi (CoinGecko 101-500)", m.emergente_oggi == True),
                  ("unione emergenti", (m.emergente_storico == True) | (m.emergente_oggi == True)),
                  ("top 100 di oggi (non emergenti, confronto)", (m.rank_oggi <= 100))):
    x = m[sel]; hd = x[x.classe != "senza dati"]; fv = x[x.completa_da.notna()]
    p(f"\n{name}: {len(x)} monete · con dati {len(hd)} · con perp e taker buy {int((hd.anni_perp_tbv > 0).sum())} · versione completa W3.2 {len(fv)}"
      f" · con ingressi {int((x.n_ingressi > 0).sum())} · perp oggi Bitget {int(x.bitget_perp.sum())} / OKX {int(x.okx_perp.sum())} / almeno uno {int((x.bitget_perp | x.okx_perp).sum())}")
    p(f"  classi: {x.classe.value_counts().to_dict()}")
    if len(hd): p(f"  storia prezzi mediana {hd.anni_prezzi.median():.2f} anni (quartili {hd.anni_prezzi.quantile(.25):.2f}/{hd.anni_prezzi.quantile(.75):.2f}); perp con taker mediana {hd.anni_perp_tbv.median():.2f}; versione completa mediana {fv.anni_completa.median():.2f} anni")
    if len(fv): p(f"  distanza mediana dello stop per moneta: mediana {fv.dist_stop_mediana.median():.3f} (quartili {fv.dist_stop_mediana.quantile(.25):.3f}/{fv.dist_stop_mediana.quantile(.75):.3f}); monete con stop mediano oltre la liquidazione 2x {int((fv.dist_stop_mediana > .49).sum())}, 5x {int((fv.dist_stop_mediana > .19).sum())} su {int(fv.dist_stop_mediana.notna().sum())}")
p("\nINGRESSI W3.2 (tutta la storia di ogni moneta, dal suo inizio completo; nessun esito)")
for name, sel in (("emergenti al segnale (rank 101-200 nella classifica più recente)", s.emergente_pit == True),
                  ("emergenti oggi 101-500", s.emergente_oggi == True), ("tutti", s.ticker == s.ticker)):
    x = s[sel & (s.ingresso >= "2021-01-01")]
    for side in ("long", "short", "entrambi"):
        y = x if side == "entrambi" else x[x.lato == side]
        if not len(y): continue
        p(f"  {name} · {side}: {len(y)} ingressi su {y.ticker.nunique()} monete · stop mediano {y.dist_stop.median():.3f} · oltre liq 2x {int((y.dist_stop > .49).sum())} ({(y.dist_stop > .49).mean() * 100:.0f}%; con mantenimento 2,5% {(y.dist_stop > .475).mean() * 100:.0f}%) · oltre liq 5x {int((y.dist_stop > .19).sum())} ({(y.dist_stop > .19).mean() * 100:.0f}%; {(y.dist_stop > .175).mean() * 100:.0f}%) · esposizione 1x mediana {y.esposizione_1x.median():.2f}"
          f" · BTC con/contro/flat {int((y.btc == 'con').sum())}/{int((y.btc == 'contro').sum())}/{int((y.btc == 'flat').sum())} · storia < 52 sett. {int((y.sett_storia < 52).sum())} · vol90 mediano {y.vol90_mn.median():.1f} M$ (quartili {y.vol90_mn.quantile(.25):.1f}/{y.vol90_mn.quantile(.75):.1f}) · listato Bitget o OKX al segnale {int((y.bitget_listato | y.okx_listato).sum())}")
x = s[(s.emergente_pit == True) & (s.ingresso >= "2021-01-01")]
p("\nLeva massima compatibile con lo stop (1/(d+0,05)), ingressi emergenti al segnale:", pd.cut(1 / (x.dist_stop + 0.05), [0, 1, 2, 5, 99], labels=["<1x", "1-2x", "2-5x", ">=5x"]).value_counts().sort_index().to_dict())
p("Posizioni simultanee (emergenti al segnale, durata non usata: solo ingressi per settimana) · ingressi nella stessa settimana: mediana",
  x.groupby("segnale").size().median(), "max", x.groupby("segnale").size().max())
(D / "summary.txt").write_text("\n".join(L) + "\n"); print("\n".join(L))

# idonee in avanti al 1° gennaio (punto nel tempo): rank 101-200 nella classifica di quell'anno, dati vivi, versione completa
L2 = ["\nIDONEE IN AVANTI AL 1° GENNAIO (classifica dell'anno: 101-200; tra parentesi 101-200 con dati vivi al 1/1 · con versione completa W3.2 prima del 1/1 · con ≥ 52 settimane di prezzi · perp oggi su Bitget/OKX)"]
mm = u.merge(c[["ticker", "dati_da", "dati_a", "completa_da"]], on="ticker", how="left")
for Y in range(2021, 2027):
    y0 = pd.Timestamp(f"{Y}-01-01"); col = f"rank_{Y}"
    e = mm[(mm[col] > 100) & (mm[col] <= 200)]
    live = e[e.dati_da.notna() & (pd.to_datetime(e.dati_da) <= y0) & (pd.to_datetime(e.dati_a) >= y0)]
    full = live[live.completa_da.notna() & (pd.to_datetime(live.completa_da) <= y0)]
    h52 = live[pd.to_datetime(live.dati_da) <= y0 - pd.Timedelta(weeks=52)]
    yy = s[(s.anno == Y) & (s.emergente_pit == True)]
    L2.append(f"  {Y}: 101-200 incluse {len(e)} · dati vivi {len(live)} · completa {len(full)} · ≥52 sett. {len(h52)} · perp oggi Bitget/OKX {int((full.bitget_perp | full.okx_perp).sum())}"
              f" | ingressi dell'anno da emergenti al segnale: long {int((yy.lato == 'long').sum())}, short {int((yy.lato == 'short').sum())}"
              f" (long contro BTC {int(((yy.lato == 'long') & (yy.btc == 'contro')).sum())}, short contro BTC {int(((yy.lato == 'short') & (yy.btc == 'contro')).sum())})")
with open(D / "summary.txt", "a") as fh: fh.write("\n".join(L2) + "\n")
print("\n".join(L2))
