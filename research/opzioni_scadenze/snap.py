"""Istantanea delle scadenze BTC su Deribit: open interest, put/call, massimo dolore, muri, volatilità attesa, movimento atteso.
Uso: python3 snap.py  -> dati/snap_<ora>.json e stampa. Solo API pubblica Deribit."""
import json, math, sys, time, datetime as dt, collections, requests
API = "https://www.deribit.com/api/v2/public/"
H = {"User-Agent": "radar-research/1.0"}
def get(m, **p):
    r = requests.get(API + m, params=p, headers=H, timeout=30); r.raise_for_status(); return r.json()["result"]
def main():
    now = dt.datetime.now(dt.timezone.utc)
    S = get("get_index_price", index_name="btc_usd")["index_price"]
    book = get("get_book_summary_by_currency", currency="BTC", kind="option")
    ex = collections.defaultdict(list)
    for x in book:
        _, e, k, cp = x["instrument_name"].split("-")
        ex[e].append(dict(k=float(k), cp=cp, oi=x["open_interest"] or 0, iv=x.get("mark_iv"), vol=x.get("volume") or 0,
                          und=x.get("underlying_price")))
    out = []
    for e, L in ex.items():
        T = dt.datetime.strptime(e, "%d%b%y").replace(hour=8, tzinfo=dt.timezone.utc)
        days = (T - now).total_seconds() / 86400
        if days < -0.01: continue
        c = sum(o["oi"] for o in L if o["cp"] == "C"); p = sum(o["oi"] for o in L if o["cp"] == "P")
        ks = sorted({o["k"] for o in L})
        def pain(s): return sum(o["oi"] * (max(s - o["k"], 0) if o["cp"] == "C" else max(o["k"] - s, 0)) for o in L)
        mp = min(ks, key=pain)
        und = next((o["und"] for o in L if o["und"]), S)
        atm = min(ks, key=lambda k: abs(k - und))
        ivs = [o["iv"] for o in L if o["k"] == atm and o["iv"]]
        iv = sum(ivs) / len(ivs) if ivs else None
        mv = und * iv / 100 * math.sqrt(max(days, 0.01) / 365) if iv else None
        def topk(cp): return [(o["k"], round(o["oi"])) for o in sorted([o for o in L if o["cp"] == cp], key=lambda o: -o["oi"])[:3]]
        # skew 25d approssimato: IV put 10% fuori - IV call 10% fuori
        def ivat(cp, k0):
            cand = [o for o in L if o["cp"] == cp and o["iv"]]
            return min(cand, key=lambda o: abs(o["k"] - k0))["iv"] if cand else None
        pu, ca = ivat("P", und * 0.9), ivat("C", und * 1.1)
        out.append(dict(scadenza=e, data=T.strftime("%Y-%m-%d"), giorni=round(days, 2), oi_call=round(c), oi_put=round(p),
                        nozionale_musd=round((c + p) * S / 1e6), put_call=round(p / c, 2) if c else None, max_pain=mp,
                        dist_max_pain_pct=round((mp / S - 1) * 100, 1), futuro=round(und), iv_atm=iv and round(iv, 1),
                        mov_atteso_usd=mv and round(mv), mov_atteso_pct=mv and round(mv / und * 100, 1),
                        skew_put10_call10=(pu and ca) and round(pu - ca, 1), muri_call=topk("C"), muri_put=topk("P")))
    out.sort(key=lambda r: r["giorni"])
    dv = get("get_volatility_index_data", currency="BTC", start_timestamp=int((time.time() - 7200) * 1000),
             end_timestamp=int(time.time() * 1000), resolution="3600")["data"]
    res = dict(ora_utc=now.strftime("%Y-%m-%d %H:%M"), indice=S, dvol=dv[-1][4] if dv else None, scadenze=out)
    fn = f"dati/snap_{now.strftime('%Y%m%d_%H%M')}.json"; json.dump(res, open(fn, "w"), indent=1)
    print(json.dumps(res, indent=1)); return res
if __name__ == "__main__": main()
