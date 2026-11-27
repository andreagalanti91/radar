"""emergenti · dati Binance dall'archivio pubblico data.binance.vision (spot 1d con taker buy, perp USDT-M 1d con taker buy,
funding mensile), con il codice di research/w32_asset2/crypto/fetch.py (stessi formati, stessa fine LAST = 2026-11-24, User-Agent
onesto, pause). Le serie già scaricate da w32_asset2 (data/raw/bn, stessa fonte e stessa fine) si riusano senza riscaricarle;
qui si scaricano solo i simboli nuovi in data/raw/bn/ (fuori da git). Uso: python3 fetch.py"""
import json, sys
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pandas as pd
HERE = Path(__file__).resolve().parent; W32 = HERE.parent / "w32_asset2" / "crypto"
sys.path.insert(0, str(W32))
import fetch as F  # noqa: E402
F.BN = HERE / "data" / "raw" / "bn"; F.BN.mkdir(parents=True, exist_ok=True)
OLD = W32 / "data" / "raw" / "bn"

if __name__ == "__main__":
    u = pd.read_csv(HERE / "data" / "universe_raw.csv"); u = u[u.escluso.isna()]
    jobs = []
    for r in u.itertuples():
        for c in json.loads(r.chain):
            if c["spot"]: jobs.append((c["spot"], "spot"))
            if c["perp"]: jobs += [(c["perp"], "perp"), (c["perp"], "funding")]
    jobs = sorted({j for j in jobs if not (OLD / f"{j[0]}_{j[1]}.csv.gz").exists()})
    print(len(jobs), "serie nuove", flush=True)
    with ThreadPoolExecutor(12) as ex:
        for r in ex.map(F.safe, jobs, [{}] * len(jobs)): print(*r, flush=True)
