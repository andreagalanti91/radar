"""Punto 1: riproduzione della v1 sul file dell'utente e sui dati di Radar."""
import pandas as pd

from common import V, IMP, user_daily, radar_daily

D = user_daily()
S = V.simulate(D)
m = V.metrics(S["equity"], S["trades"])
ns = sum(t["verso"] == "short" for t in S["trades"])
print("UTENTE  fino al", D.index[-1].date(), "| finale", m["finale_10k"], "| oper.", m["operazioni"], "| short", ns,
      "| CAGR %.1f%% | DD %.1f%%" % (m["cagr"] * 100, m["dd"] * 100))
ref = pd.read_csv(IMP / "v1_operazioni_2018_2026.csv")
mine = pd.DataFrame(S["trades"])
same = (mine[["verso", "entra", "esce"]].fillna("").astype(str).values == ref[["verso", "entra", "esce"]].fillna("").astype(str).values).all()
print("operazioni identiche al file dell'utente:", bool(same), "| max diff risultato:", float((mine["risultato"] - ref["risultato"]).abs().max()))

R = radar_daily()
print("RADAR   dati", R.index[0].date(), "->", R.index[-1].date())
end = min(D.index[-1], R.index[-1])
Du, Dr = D.loc[:end], R.loc[:end]
print("  stesse date:", Du.index.equals(Dr.index))
for col in ("open", "high", "low", "close", "volume"):
    print(f"  max |diff| {col}: {(Du[col] - Dr[col]).abs().max():.6g}")
fu_u, fu_r = Du["funding"], Dr["funding"].fillna(V.FUND_DEFAULT)
print("  max |diff| funding (Radar vuoto -> 0,03%):", float((fu_u - fu_r).abs().max()))
Su, Sr = V.simulate(Du), V.simulate(Dr)
mu, mr = V.metrics(Su["equity"], Su["trades"]), V.metrics(Sr["equity"], Sr["trades"])
print("  fino al", end.date(), "| utente", mu["finale_10k"], mu["operazioni"], "| Radar", mr["finale_10k"], mr["operazioni"],
      "| CAGR %.2f/%.2f DD %.2f/%.2f" % (mu["cagr"] * 100, mr["cagr"] * 100, mu["dd"] * 100, mr["dd"] * 100))
print("  operazioni identiche:", [(t["entra"], t["esce"]) for t in Su["trades"]] == [(t["entra"], t["esce"]) for t in Sr["trades"]])
print("  max diff voto dal 2018:", float((Su["score"].loc["2018":] - Sr["score"].loc["2018":]).abs().max()))
# il giorno in più del file dell'utente (22/11): Radar lo avrà al prossimo aggiornamento di data/spot.csv
Dx = pd.concat([Dr, D.loc[D.index > end]])
Sx = V.simulate(Dx)
mx = V.metrics(Sx["equity"], Sx["trades"])
print("  Radar + 22/11 dell'utente:", mx["finale_10k"], mx["operazioni"], "%.1f%% %.1f%%" % (mx["cagr"] * 100, mx["dd"] * 100))
