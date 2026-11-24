"""tradera_test · fase 1: il rilevatore ritrova gli esempi di TraderA? Output: replica.txt. Uso: python3 tt_replica.py
Prezzi delle azioni NON rettificati per i dividendi (come il grafico di TradingView)."""
from __future__ import annotations

import itertools
import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fetch  # noqa: E402
import tt_detect as T  # noqa: E402

OUT = []
TRADER = dict(A=("2026-03", 683.0), B=("2026-08", 610.0), entry=567.93, stop=539.57, tgt=688.69,
              s_entry=567.65, s_stop=585.13, s_tgt=499.69)
NVZ = [(140, 150), (88, 95), (44, 50), (29, 33)]


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def pct(a, b):
    return f"{100 * (a / b - 1):+.2f}%"


def lmt(p: dict | None = None, verbose: bool = False) -> dict:
    d = fetch.stock("LMT", raw=True)
    d = d[d.index >= "2015-01-01"]
    r = T.detect(d, p)
    ix = d.index
    # piano del trader mostrato sul grafico del 13/11 (prezzo 595): segnale del rilevatore entro quella data
    s = [x for x in r["signals"] if x["side"] == 1 and pd.Timestamp("2026-10-01") <= ix[x["t"]] <= pd.Timestamp("2026-11-20")]
    if not s:
        return dict(ok=False)
    s = s[-1]
    t = s["t"]
    entry = float(d["open"].iloc[t + 1]) if t + 1 < len(d) else float("nan")
    res = dict(ok=True, A=(ix[s["iA"]].date(), s["pA"]), B=(ix[s["iB"]].date(), s["pB"]), brk=ix[s["ib"]].date(),
               sig=ix[t].date(), lv=s["lv"], entry=entry, stop=s["stop"], tgt=s["tgt"], conf=s["conf"],
               rr=(s["tgt"] - entry) / (entry - s["stop"]), e50=s["e50"], e200=s["e200"], atr=s["atr"])
    # piano speculare ipotetico (non ancora scattato): soglia, stop e obiettivo se oggi la linea cedesse
    t2 = len(d) - 1
    m = (s["pB"] - s["pA"]) / (s["iB"] - s["iA"])
    res["lv_today"] = s["pA"] + m * (t2 - s["iA"])
    res["flip_trigger"] = res["lv_today"] - T.P["INV"] * r["atr"][t2] if not p else float("nan")
    res["flip_tgt"] = float(d["low"].iloc[s["iB"]:s["ib"] + 1].min())
    res["flip_stop_now"] = float(d["high"].iloc[t2 - T.P["BASE"] + 1:t2 + 1].max()) * (1 + T.P["MARG"])
    return res


def match(r: dict) -> bool:
    return (r.get("ok") and str(r["A"][0])[:7] == "2026-03" and str(r["B"][0])[:7] == "2026-08"
            and abs(r["entry"] / TRADER["entry"] - 1) < 0.01 and abs(r["stop"] / TRADER["stop"] - 1) < 0.01
            and abs(r["tgt"] / TRADER["tgt"] - 1) < 0.01)


def main():
    say("=== FASE 1 · replica degli esempi di TraderA (parametri:", T.P, ")")
    r = lmt()
    say("\n[LMT giornaliero, prezzi non rettificati]")
    say(f"(1) linea: A {r['A'][0]} {r['A'][1]:.2f} (trader ~683, marzo) · B {r['B'][0]} {r['B'][1]:.2f} (trader ~610, agosto)")
    say(f"    rottura (prima chiusura sopra la linea): {r['brk']}; slancio fino a 657 il 30/10")
    say(f"(2) ritest confermato il {r['sig']} (linea {r['lv']:.2f}, confluenza EMA50/200 entro 1 ATR: {r['conf']}; "
        f"EMA50 {r['e50']:.1f}, EMA200 {r['e200']:.1f}, ATR {r['atr']:.1f}); ingresso all'apertura dopo: {r['entry']:.2f} "
        f"(trader 567,93 → {pct(r['entry'], TRADER['entry'])})")
    say(f"(3) stop {r['stop']:.2f} (trader 539,57 → {pct(r['stop'], TRADER['stop'])}) = minimo delle 3 barre prima della rottura "
        f"− 0,1%; obiettivo {r['tgt']:.2f} = punto A (trader 688,69 → {pct(r['tgt'], TRADER['tgt'])}); R:R {r['rr']:.2f} (trader 4,3)")
    say(f"    piano speculare (non scattato): linea oggi {r['lv_today']:.2f}; scatta con chiusura < {r['flip_trigger']:.2f}; "
        f"obiettivo {r['flip_tgt']:.2f} (trader 499,69 → {pct(r['flip_tgt'], TRADER['s_tgt'])}); stop = massimo 3 barre "
        f"+0,1% (oggi {r['flip_stop_now']:.2f}; trader 585,13)")
    # sensibilità: quali combinazioni dei parametri liberi riproducono LMT (calibrazione dichiarata)
    say("\n[Calibrazione: combinazioni che riproducono LMT (A marzo, B agosto, ingresso/stop/obiettivo entro 1%)]")
    grid = dict(PIV=(5, 10, 15), MOM=(1.0, 1.5, 2.0), TOL=(0.25, 0.5, 1.0), INV=(0.5, 1.0), BASE=(2, 3, 5))
    ok, tot = [], 0
    for vals in itertools.product(*grid.values()):
        q = dict(zip(grid.keys(), vals))
        tot += 1
        if match(lmt(q)):
            ok.append(q)
    say(f"    {len(ok)} su {tot} combinazioni riproducono i tre numeri.")
    for k, vs in grid.items():
        say(f"    {k}: " + " · ".join(f"{v}: {sum(1 for q in ok if q[k] == v)}" for v in vs))
    # NVDA: zone al 19/11/2026 (prezzo 145,98)
    say("\n[NVDA giornaliero: zone orizzontali al 19/11/2026 (cluster di pivot settimanali, ZK 3, ZW 10%)]")
    d = fetch.stock("NVDA", raw=True)
    say(f"    chiusura 19/11/2026: {d.loc['2026-11-19', 'close']:.2f} (trader 145,98); 20/11: {d.loc['2026-11-20', 'close']:.2f}")
    z = [x for x in T.zones(d, "2026-11-19") if x["hi"] >= 20 and x["lo"] <= 260]
    say("    zone del rilevatore: " + "; ".join(f"{x['lo']:.1f}–{x['hi']:.1f} ({x['n']})" for x in z))
    for lo, hi in NVZ:
        best = min(z, key=lambda x: max(0.0, max(lo, x["lo"]) - min(hi, x["hi"])) * 0 + abs((x["lo"] + x["hi"]) / 2 - (lo + hi) / 2))
        ov = max(0.0, min(hi, best["hi"]) - max(lo, best["lo"]))
        say(f"    trader {lo}–{hi}: zona più vicina {best['lo']:.1f}–{best['hi']:.1f}; sovrapposizione {ov:.1f} $ "
            f"({'coincide' if ov > 0 else 'vicino' if abs((best['lo'] + best['hi']) / (lo + hi) - 1) < 0.15 else 'diverso'})")
    say("    sensibilità (ZK × ZW): quante delle 4 zone del trader si sovrappongono a una zona del rilevatore; zone totali 20–260 $")
    for zk in (3, 4, 6):
        row = []
        for zw in (0.05, 0.06, 0.08, 0.10):
            zz = [x for x in T.zones(d, "2026-11-19", dict(ZK=zk, ZW=zw)) if x["hi"] >= 20 and x["lo"] <= 260]
            hit = sum(any(min(hi, x["hi"]) > max(lo, x["lo"]) for x in zz) for lo, hi in NVZ)
            row.append(f"ZW {zw:.2f}: {hit}/4 su {len(zz)}")
        say(f"    ZK {zk}: " + " · ".join(row))
    r2 = T.detect(d[d.index <= "2026-11-19"])
    say("    linee/setup del rilevatore su NVDA al 19/11: " + "; ".join(
        f"{q['kind']} lato {'long' if q['side'] > 0 else 'short'} livello {q['lv_next']:.1f}" for q in r2["pending"]))
    # BTC al 21/11/2026
    say("\n[BTC giornaliero (Binance): 21/11/2026, acquisto del trader 55.777,53, minimo 55.130]")
    b = fetch.crypto("BTCUSDT")
    bb = b[b.index <= "2026-11-21"]
    z = T.zones(b, "2026-11-21")
    inz = [x for x in z if x["lo"] <= 55777.53 <= x["hi"]]
    say("    zone vicine: " + "; ".join(f"{x['lo']:.0f}–{x['hi']:.0f} ({x['n']}, ultimo tocco {x['ultimo']})"
                                     for x in z if 45000 <= x["hi"] and x["lo"] <= 75000))
    say(f"    il prezzo d'acquisto sta in una zona: {'sì, ' + str(round(inz[0]['lo'])) + '–' + str(round(inz[0]['hi'])) if inz else 'no'}")
    rb = T.detect(bb)
    ix = bb.index
    last = [x for x in rb["signals"] + rb["flips"] if ix[x["t"]] >= pd.Timestamp("2026-10-01")]
    say("    segnali linea+ritest o piano speculare dal 01/10: " + ("; ".join(
        f"{ix[x['t']].date()} {'long' if x['side'] > 0 else 'short'} @{x['close']:.0f} (R:R {x.get('rr', float('nan')):.1f})"
        for x in last) or "nessuno"))
    say("    stato al 21/11: " + "; ".join(f"{q['kind']} lato {'long' if q['side'] > 0 else 'short'} livello {q['lv_next']:.0f}"
                                         for q in rb["pending"]))
    (HERE / "replica.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
