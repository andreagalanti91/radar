"""macd_sol · solo descrittivo, NON fa parte del giudizio del PREREG: C1 e C3 (non scelti in IS) in OOS e C3 con soglia DD vicina."""
import sys, io, contextlib
from pathlib import Path
HERE = Path(__file__).resolve().parent; sys.path.insert(0, str(HERE))
with contextlib.redirect_stdout(io.StringIO()):
    import fase2 as F  # riesegue la fase 2 (stesso output su file); qui si usano solo le sue funzioni
out = []
for cn in ("C1", "C3"):
    o, m = F.cand(cn, F.OOS_S, F.END); r24, _ = F.sub(o["equity"], F.Y24, F.END)
    out.append(f"{cn} OOS dal 01/01/2023 (non scelto, descrittivo): {m['fin']:,} $, DD {m['dd']}%, C/DD {m['cd']}, trade {m['n']}, WR chiuse {m['wr_cl']}%, 2024→ {r24}%")
    o, m = F.cand(cn, "2021-01-11", F.END)
    out.append(f"{cn} dal 11/01/2021 (descrittivo): {m['fin']:,} $, DD {m['dd']}%, C/DD {m['cd']}, trade {m['n']}, WR chiuse {m['wr_cl']}%")
d = F.tradelist(F.all_tr(F.cand("C3", "2021-01-11", F.END)[0]), "C3_descrittivo")
out.append("Operazioni C3 dal 11/01/2021 (descrittivo)\n" + F.mdt(d))
txt = "\n".join(out); print(txt); (HERE / "descrittivi_output.txt").write_text(txt + "\n")
