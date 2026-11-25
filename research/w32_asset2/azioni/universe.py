"""W3.2 asset ciclo 2 · azioni · fase dati: classifica per capitalizzazione OGGI e al 31/12/2019 (= 01/01/2020).

Fonte unica, pubblica e leggibile senza login: CompaniesMarketcap.com (robots.txt consente le pagine usate; Terms of Service
del 10/11/2023: nessun divieto di lettura automatica, riuso con attribuzione). Lettura lenta (pausa 1,5 s), User-Agent generico
onesto, una pagina per richiesta, copia locale in cache fuori dal repo; nel repo si salvano solo i valori estratti.
- Oggi: CSV offerto dal sito (pulsante "download", https://companiesmarketcap.com/?download=csv) + pagine della classifica 1-5
  (500 società) per il collegamento alla pagina della società.
- 31/12/2019: tabella "market cap at the end of each year" della pagina /<società>/marketcap/ di ciascun candidato.
  Candidati = prime 500 di oggi + società grandi nel 2019 che oggi possono essere fuori dalle prime 500 (EXTRA).
  Limite dichiarato: una società con capitalizzazione 2019 nella top 100 e oggi fuori dalle prime 500 e fuori da EXTRA sfugge.
Uscita: data/cmc_today.csv (prime 500 di oggi), data/cmc_2019.csv (capitalizzazione a fine 2019 dei candidati).
"""
from __future__ import annotations

import html
import re
import sys
import time
from pathlib import Path

import pandas as pd
import requests

HERE = Path(__file__).resolve().parent
D = HERE / "data"
CACHE = Path(sys.argv[1]) if len(sys.argv) > 1 else Path("/tmp/cmc_cache")
UA = {"User-Agent": "research-client/1.0"}
BASE = "https://companiesmarketcap.com"
# società che a fine 2019 erano vicine o dentro la top 100 e potrebbero essere scese molto (Russia, fusioni)
EXTRA = ["sberbank", "gazprom", "rosneft", "lukoil", "novatek", "naspers", "prosus", "bayer", "intel", "boeing",
         "walgreens-boots-alliance", "3m", "verizon", "pfizer", "petrobras", "vale", "bp", "bhp-group",
         "ambev", "itau-unibanco", "british-american-tobacco", "gilead-sciences", "cvs-health", "sinopec",
         "china-life-insurance", "baidu", "kddi", "ntt-docomo", "nippon-telegraph-and-telephone", "softbank", "starbucks"]


def get(url: str, name: str) -> str:
    CACHE.mkdir(parents=True, exist_ok=True)
    p = CACHE / name
    if p.exists():
        return p.read_text()
    for k in range(3):
        try:
            r = requests.get(url, headers=UA, timeout=60)
            time.sleep(1.5)
            if r.status_code == 404:
                return ""
            r.raise_for_status()
            p.write_text(r.text)
            return r.text
        except requests.RequestException as e:
            print("  retry", url, type(e).__name__)
            time.sleep(5 * (k + 1))
    return ""


def listing() -> pd.DataFrame:
    out = []
    for pg in range(1, 6):
        t = get(f"{BASE}/" if pg == 1 else f"{BASE}/page/{pg}/", f"page{pg}.html")
        for row in re.findall(r"<tr>.*?</tr>", t, flags=re.S):
            m = re.search(r'data-sort="(\d+)"[^>]*>\d+</td>.*?<a href="/([^/]+)/marketcap/"><div class="company-name">(.*?)</div>'
                          r'<div class="company-code"><span class="rank d-none"></span>(.*?)</div>.*?data-sort="(\d+)"', row, re.S)
            if m:
                cty = re.findall(r'<span class="responsive-hidden">(.*?)</span>', row)
                out.append(dict(rank_today=int(m.group(1)), slug=m.group(2), name=html.unescape(m.group(3)),
                                cmc_symbol=html.unescape(m.group(4)), mcap_today=float(m.group(5)), country=cty[-1] if cty else ""))
    return pd.DataFrame(out)


UNIT = {"T": 1e12, "B": 1e9, "M": 1e6, "K": 1e3}


def year_end(slug: str, year: int = 2019) -> tuple[float | None, str]:
    t = get(f"{BASE}/{slug}/marketcap/", f"{slug}.html")
    if not t:
        return None, ""
    name = re.search(r"<h1[^>]*>(.*?)</h1>", t, re.S)
    name = re.sub(r"<[^>]+>", " ", name.group(1)).strip() if name else slug
    for row in re.findall(r"<tr>.*?</tr>", t, flags=re.S):
        s = re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", row)).strip()
        m = re.match(rf"{year} \$([\d.,]+) ([TBMK])\b", s)
        if m:
            return float(m.group(1).replace(",", "")) * UNIT[m.group(2)], html.unescape(name)
    return None, html.unescape(name)


if __name__ == "__main__":
    D.mkdir(parents=True, exist_ok=True)
    lst = listing()
    print("classifica di oggi:", len(lst), "società lette")
    lst.to_csv(D / "cmc_today.csv", index=False)
    rows = []
    slugs = list(dict.fromkeys(list(lst["slug"]) + EXTRA))
    for i, s in enumerate(slugs):
        v, nm = year_end(s)
        rows.append(dict(slug=s, page_title=nm, mcap_2019=v))
        if i % 50 == 0:
            print(i, s, v)
    out = pd.DataFrame(rows)
    out["page_title"] = out["page_title"].astype(str).str.split().str.join(" ")
    out.to_csv(D / "cmc_2019.csv", index=False)
