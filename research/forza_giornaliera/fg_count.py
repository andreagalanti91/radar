"""Conteggi PRIMA del PREREG: solo numerosità di eventi, nessun rendimento. Output: conteggi.txt. Uso: python3 fg_count.py"""
from __future__ import annotations

import sys
from pathlib import Path

import pandas as pd

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
import fg_lib as G  # noqa: E402

OUT = []


def say(*a):
    s = " ".join(str(x) for x in a)
    print(s)
    OUT.append(s)


def halves(days):
    a = sum(1 for d in days if d < pd.Timestamp(G.SPLIT))
    return f"{len(days)} ({a}/{len(days) - a})"


def main():
    for name, f0 in (("BTC", G.btc()), ("ETH", G.eth())):
        f = G.add_flows(f0)
        s = f[(f.index >= G.START)]
        say(f"== {name} · {s.index[0].date()} → {s.index[-1].date()} · {len(s)} giorni · primo pz3 valido {f['pz3'].first_valid_index().date()}")
        say("-- H1/H2: primo giorno con movimento ≥ X in N giorni (pausa 7 g); n totale (2021–23 / 2024→) e classi perp/spot/misto")
        for side, lab in ((1, "rialzo"), (-1, "ribasso")):
            for n in (2, 3, 5):
                for x in (0.04, 0.05, 0.06, 0.08):
                    cond = (s[f"up{n}"] >= x) if side > 0 else (s[f"dn{n}"] <= -x)
                    days = G.first_days(cond)
                    row = f"{lab} N={n} X={int(x * 100)}%: {halves(days)}"
                    for d0 in (0.5, 1.0):
                        k = G.klass(f, n, side, d0).reindex(days)
                        row += f" | D0={d0}: " + " ".join(f"{c} {halves([d for d in days if k[d] == c])}" for c in ("perp", "spot", "misto"))
                    kt = G.klass_trader(f, n, side).reindex(days)
                    row += " | trader$: " + " ".join(f"{c} {halves([d for d in days if kt[d] == c])}" for c in ("perp", "spot", "misto"))
                    say(row)
        say("-- H3: rottura in chiusura del massimo/minimo dei 20 (10) giorni precedenti (pausa 7 g), conferma spot sz3 nel verso")
        for L in (10, 20):
            for side, lab in ((1, "su"), (-1, "giù")):
                cond = (s["close"] > s[f"hi{L}"]) if side > 0 else (s["close"] < s[f"lo{L}"])
                days = G.first_days(cond)
                conf = [d for d in days if s.loc[d, "sz3"] * side > 0]
                k = G.klass(f, 3, side, 0.5).reindex(days)
                say(f"rottura {L}g {lab}: {halves(days)} | con spot (sz3 nel verso) {halves(conf)} | senza {halves([d for d in days if d not in conf])}"
                    f" | classe D0=0,5: " + " ".join(f"{c} {halves([d for d in days if k[d] == c])}" for c in ("perp", "spot", "misto")))
        if name == "BTC":
            sys.path.insert(0, str(G.ROOT / "research" / "swing_sr"))
            import sw_engine as S
            sg = S.signals(f0)
            sig = sg["sig"] if isinstance(sg, dict) and "sig" in sg else None
            if sig is not None:
                idx = f0[f0["close"].notna()].index
                for side, lab in ((1, "su"), (-1, "giù")):
                    cond = pd.Series(sig[("X", side)], index=idx)
                    cond = cond[cond.index >= G.START]
                    days = G.first_days(cond)
                    conf = [d for d in days if f.loc[d, "sz3"] * side > 0]
                    say(f"rottura livello swing settimanale {lab}: {halves(days)} | con spot {halves(conf)} | senza {halves([d for d in days if d not in conf])}")
        # W3.2
        r = G.w3(f0)
        tr = G.trades(r)
        say(f"-- W3.2 {name}: {len(tr)} trade (aperto compreso) · long {sum(t['side'] == 'long' for t in tr)} short {sum(t['side'] == 'short' for t in tr)}")
        say("E-in: giorni 0..K−1 dal segnale (0 = domenica) con perp e spot nel verso (pzN·lato > 0 e szN·lato > 0); primo giorno utile per trade")
        for n in (1, 3):
            firsts = []
            for t in tr:
                sd = 1 if t["side"] == "long" else -1
                d0 = pd.Timestamp(t["signal"])
                j = next((j for j in range(0, 6) if d0 + pd.Timedelta(days=j) in f.index and f.loc[d0 + pd.Timedelta(days=j), f"pz{n}"] * sd > 0
                          and f.loc[d0 + pd.Timedelta(days=j), f"sz{n}"] * sd > 0), None)
                firsts.append(j)
            say(f"  N={n}: primo giorno concorde per trade = {firsts} (None = mai entro 5)")
        say("E-out: giorni dentro i trade con chiusura oltre il minimo/massimo dei L giorni contro la posizione; di cui vendita/acquisto contrario "
            "guidato dallo spot (classe 'spot', D0=0,5), 'con spot' (sz3 contrario), 'solo perp' (classe 'perp')")
        for L in (10, 20):
            tot = sp = cs = pp = 0
            ntr = set()
            for t in tr:
                sd = 1 if t["side"] == "long" else -1
                a, b = pd.Timestamp(t["entry"]), pd.Timestamp(t["exit"]) if t["exit"] else f.index[-1]
                seg = f[(f.index >= a) & (f.index < b)]
                brk = (seg["close"] < seg[f"lo{L}"]) if sd > 0 else (seg["close"] > seg[f"hi{L}"])
                k = G.klass(f, 3, -sd, 0.5).reindex(seg.index)
                tot += int(brk.sum()); sp += int((brk & (k == "spot")).sum()); pp += int((brk & (k == "perp")).sum())
                cs += int((brk & (seg["sz3"] * -sd > 0)).sum())
                if (brk & (k == "spot")).any():
                    ntr.add(t["signal"])
            say(f"  L={L}: giorni di rottura {tot} · guidati dallo spot {sp} (in {len(ntr)} trade) · con spot {cs} · solo perp {pp}")
        say("E-hold: movimenti contrari ≥ 5% in 3 giorni dentro i trade (primo giorno, pausa 7 g) per classe (D0=0,5)")
        cnt = {"perp": 0, "spot": 0, "misto": 0, "nd": 0}
        for t in tr:
            sd = 1 if t["side"] == "long" else -1
            a, b = pd.Timestamp(t["entry"]), pd.Timestamp(t["exit"]) if t["exit"] else f.index[-1]
            seg = f[(f.index >= a) & (f.index < b)]
            cond = (seg["dn3"] <= -0.05) if sd > 0 else (seg["up3"] >= 0.05)
            k = G.klass(f, 3, -sd, 0.5)
            for d in G.first_days(cond):
                cnt[k[d]] += 1
        say(f"  {cnt}")
    (HERE / "conteggi.txt").write_text("\n".join(OUT) + "\n")


if __name__ == "__main__":
    main()
