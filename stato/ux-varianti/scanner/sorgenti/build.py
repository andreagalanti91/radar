"""build.py: copia del template con il blocco #scPos (variante 1 o 2) in stato/ux-varianti/scanner/."""
from pathlib import Path
T = Path("/home/user/radar/radar/dashboard_template.html").read_text()
H = Path(__file__).parent
js, css = (H / "pos.js").read_text(), (H / "pos.css").read_text()
OUT = Path("/home/user/radar/stato/ux-varianti/scanner"); OUT.mkdir(parents=True, exist_ok=True)
for v in (1, 2):
    t = T
    a = '      <div id="scIng"></div>\n'; assert t.count(a) == 1; t = t.replace(a, a + '      <div id="scPos"></div>\n')
    a = "</style>"; i = t.index(a); t = t[:i] + css + t[i:]
    a = "  drawIng();\n"; assert t.count(a) == 1; t = t.replace(a, a + "\n" + js.replace("__VAR__", str(v)))
    (OUT / f"variante{v}_template.html").write_text(t)
print("ok")
