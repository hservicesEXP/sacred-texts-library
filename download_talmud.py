"""
Downloader Talmud Bavli (solo ebraico/aramaico, niqqud) - bucket GCS
pubblico gs://sefaria-export/json/, stesso identico pattern gia' usato
per il PDF bilingue (download bulk, non API REST). Qui scarichiamo SOLO
il lato ebraico (William Davidson Edition - Vocalized Aramaic) dei 37
trattati, per la libreria in sola lingua originale: nessuna traduzione
inglese scaricata.

Idempotente: --skip-existing salta i file gia' presenti con size
corretto. Stampa SOLO tabella trattato -> KB -> stato a fine corsa.
"""
import argparse
import json
import urllib.parse
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "talmud_he"

BASE = "https://storage.googleapis.com/storage/v1/b/sefaria-export/o"
DL_BASE = "https://storage.googleapis.com/download/storage/v1/b/sefaria-export/o"

SEDARIM = [
    "Seder Zeraim", "Seder Moed", "Seder Nashim", "Seder Nezikin",
    "Seder Kodashim", "Seder Tahorot",
]
HE_VERSION = "William Davidson Edition - Vocalized Aramaic.json"


def list_gcs(prefix, delimiter=None):
    url = f"{BASE}?prefix={urllib.parse.quote(prefix)}"
    if delimiter:
        url += f"&delimiter={urllib.parse.quote(delimiter)}"
    items, prefixes = [], []
    page_token = None
    while True:
        u = url + (f"&pageToken={page_token}" if page_token else "")
        with urllib.request.urlopen(u) as r:
            d = json.load(r)
        items.extend(d.get("items", []))
        prefixes.extend(d.get("prefixes", []))
        page_token = d.get("nextPageToken")
        if not page_token:
            break
    return items, prefixes


def gcs_name_to_download_url(name):
    return f"{DL_BASE}/{urllib.parse.quote(name, safe='')}?alt=media"


def build_manifest():
    manifest = {}
    order = 0
    for seder in SEDARIM:
        _, prefixes = list_gcs(f"json/Talmud/Bavli/{seder}/", delimiter="/")
        tractates = sorted(p.split("/")[-2] for p in prefixes)
        for tractate in tractates:
            he_items, _ = list_gcs(f"json/Talmud/Bavli/{seder}/{tractate}/Hebrew/")
            he_hit = next((i for i in he_items if i["name"].endswith(HE_VERSION)), None)
            if not he_hit:
                raise SystemExit(f"Versione ebraica mancante per {tractate}")
            manifest[tractate] = {
                "seder": seder,
                "order": order,
                "he_url": gcs_name_to_download_url(he_hit["name"]),
                "he_size": int(he_hit["size"]),
            }
            order += 1
    return manifest


def download(url, dest: Path, expected_size: int, skip_existing: bool):
    if skip_existing and dest.exists() and dest.stat().st_size == expected_size:
        return "skip-existing"
    dest.parent.mkdir(parents=True, exist_ok=True)
    tmp = dest.with_suffix(dest.suffix + ".part")
    with urllib.request.urlopen(url, timeout=120) as r, open(tmp, "wb") as f:
        while True:
            chunk = r.read(1 << 16)
            if not chunk:
                break
            f.write(chunk)
    tmp.replace(dest)
    return "downloaded"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    manifest = build_manifest()
    manifest_path = ROOT / "data" / "talmud_he_manifest.json"
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(json.dumps(manifest, ensure_ascii=False, indent=1), encoding="utf-8")

    print(f"{'trattato':<20} {'KB':>10} {'stato':>14}")
    total_kb = 0.0
    for tractate, info in sorted(manifest.items(), key=lambda kv: kv[1]["order"]):
        dest = DATA_DIR / f"{tractate}.json"
        status = download(info["he_url"], dest, info["he_size"], args.skip_existing)
        kb = dest.stat().st_size / 1024
        total_kb += kb
        print(f"{tractate:<20} {kb:>10.1f} {status:>14}")
    print(f"{'TOTALE':<20} {total_kb:>10.1f}")


if __name__ == "__main__":
    main()
