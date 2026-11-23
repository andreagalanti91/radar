"""trend_multi · U2 "elenco di oggi" (descrittivo, OTTIMISTICO). Deviazione dall'ADDENDUM: l'elenco completo (211 ticker comuni a
OKX e Bitget) non è scaricabile (limite di frequenza di Yahoo): si usano le 10 maggiori capitalizzazioni di oggi già in
research/multi_asset/data (tutte con perpetuo su OKX e Bitget) + le 6 materie prime. Uscita: risultati_oggi.txt."""
import numpy as np, pandas as pd
import tm_lib as T, tm_study as S
OUT = T.D.parent; MA = OUT.parent / "multi_asset" / "data"
ST = "NVDA AAPL MSFT GOOGL AMZN META AVGO TSLA BRK-B LLY".split()
COMM = {"ORO": "GLD", "ARGENTO": "SLV", "PETROLIO": "USO", "GAS": "UNG", "RAME": "CPER", "PLATINO": "PPLT"}
extra = {s: MA / f"{s}.csv.gz" for s in ST}
extra.update({k: (T.D / f"{v}.csv.gz" if v in ("GLD", "SLV", "USO") else T.D / "u2" / f"{v}.csv.gz") for k, v in COMM.items()})
pxa, rf, _, first = T.load(extra); px = pxa[ST + list(COMM)]; zero = rf * 0
log = ["Avvio: " + str({k: str(first[k].date()) for k in ST})]
for fund in (0.05, 0.0, 0.10):
    R = {"V1 long/flat": T.run(px, rf, cash_ret=zero, fund_long=fund), "V2 long/short": T.run(px, rf, side="LS", cash_ret=zero, fund_long=fund),
         "Equipesato": T.run(px, rf, fixed=T.fixed_ew, cash_ret=zero, fund_long=fund)}
    log.append(f"\n== funding long {fund * 100:.0f}% · giudizio 2016–26 ==")
    log.append(S.fmt(pd.DataFrame([S.row(k, r["eq"], rf, T.J0, T.J1) for k, r in R.items()])))
    for a, b in (("2016-01-01", "2020-12-31"), ("2021-01-01", T.J1)):
        log.append(f"-- {a[:4]}–{b[:4]}"); log.append(S.fmt(pd.DataFrame([S.row(k, r["eq"], rf, a, b) for k, r in R.items()])))
print("\n".join(log)); (OUT / "risultati_oggi.txt").write_text("\n".join(log))
