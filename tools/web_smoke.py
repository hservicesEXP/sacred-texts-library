from pathlib import Path
import json, re, sys

ROOT = Path(__file__).resolve().parents[1]
DOCS = ROOT / "docs"

errors = []

for rel in ["reader.html", "assets/reader.js", "assets/app.js", "sw.js"]:
    if not (DOCS / rel).exists():
        errors.append(f"missing: docs/{rel}")

# Find an existing Quran data directory without assuming its layout.
candidates = [
    DOCS/"data",
    DOCS/"data"/"quran",
    DOCS/"data"/"surahs",
    DOCS/"data"/"surah",
]
json_files = []
for d in candidates:
    if d.exists():
        json_files.extend(d.glob("*.json"))

# The test is deliberately non-destructive: it validates the corpus if present,
# but does not fabricate missing Quran data.
if not json_files:
    errors.append("no Quran JSON files found under docs/data; do not deploy until corpus files are present")

# Check index candidates.
index_candidates = [
    DOCS/"data"/"index.json",
    DOCS/"data"/"quran"/"index.json",
    DOCS/"data"/"search"/"index.json",
]
index_found = False
for p in index_candidates:
    if p.exists():
        index_found = True
        try:
            raw = json.loads(p.read_text(encoding="utf-8"))
            items = raw if isinstance(raw, list) else raw.get("verses") or raw.get("items") or raw.get("index")
            if not isinstance(items, list):
                errors.append(f"invalid index structure: {p}")
            elif len(items) != 6236:
                errors.append(f"index has {len(items)} records, expected 6236: {p}")
        except Exception as e:
            errors.append(f"invalid JSON index {p}: {e}")
        break

if not index_found:
    errors.append("no Quran index.json found")

# JS syntax.
import subprocess
for rel in ["assets/reader.js", "assets/app.js", "sw.js"]:
    p = DOCS / rel
    if p.exists():
        r = subprocess.run(["node", "--check", str(p)], capture_output=True, text=True)
        if r.returncode:
            errors.append(f"node --check failed: {rel}: {r.stderr.strip()}")

if errors:
    print("FINAL WEB SMOKE: FAILED")
    for e in errors:
        print(" -", e)
    sys.exit(1)

print("FINAL WEB SMOKE: PASSED")
