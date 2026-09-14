from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
docs = ROOT / "docs"

for name in ["index.html", "reader.html", "about.html"]:
    p = docs / name
    if p.exists():
        s = p.read_text(encoding="utf-8")
        s = re.sub(r'([?&]v=)5\b', r'\g<1>6', s)
        p.write_text(s, encoding="utf-8")

css = docs / "assets/app.css"
patch = Path(__file__).resolve().parent / "final-polish.css"
if css.exists() and patch.exists():
    marker = "/* FINAL V1 POLISH PATCH */"
    s = css.read_text(encoding="utf-8")
    if marker not in s:
        s += "\n" + patch.read_text(encoding="utf-8") + "\n"
        css.write_text(s, encoding="utf-8")

print("Quran V1 repair patch applied.")
