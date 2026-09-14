"""
Downloader Hadith - AhmedBaset/hadith-json (17 raccolte, arabo+inglese
scraped da sunnah.com, JSON per libro). Fonte pinnata al tag v1.2.0
(repo raccomanda di non puntare a main).

Copre: Kutub al-Tis'ah (9 libri canonici, inclusi Musnad Ahmad e Sunan
al-Darimi non presenti nella fonte già usata per Corano) + Riyad
as-Salihin, Shamail, Bulugh al-Maram, Al-Adab Al-Mufrad, Mishkat
al-Masabih, 3 raccolte arba'in (Nawawi/Qudsi/Shah Waliullah).

Nessun filtro per grado (sahih/hasan/da'if): tutti gli ahadith della
fonte sono scaricati, il grado è un campo nei dati (se presente), non
un criterio di esclusione.

Idempotente: --skip-existing salta i file già presenti con size > 0.
Stampa SOLO la tabella file -> MB -> hadith count a fine corsa.
"""
import argparse
import json
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "hadith"

TAG = "v1.2.0"
BASE = f"https://raw.githubusercontent.com/AhmedBaset/hadith-json/{TAG}/db/by_book"

FILES = {
    # the_9_books
    "bukhari": "the_9_books/bukhari.json",
    "muslim": "the_9_books/muslim.json",
    "abudawud": "the_9_books/abudawud.json",
    "tirmidhi": "the_9_books/tirmidhi.json",
    "nasai": "the_9_books/nasai.json",
    "ibnmajah": "the_9_books/ibnmajah.json",
    "malik": "the_9_books/malik.json",
    "ahmed": "the_9_books/ahmed.json",
    "darimi": "the_9_books/darimi.json",
    # other_books
    "riyad_assalihin": "other_books/riyad_assalihin.json",
    "shamail_muhammadiyah": "other_books/shamail_muhammadiyah.json",
    "bulugh_almaram": "other_books/bulugh_almaram.json",
    "aladab_almufrad": "other_books/aladab_almufrad.json",
    "mishkat_almasabih": "other_books/mishkat_almasabih.json",
    # forties
    "nawawi40": "forties/nawawi40.json",
    "qudsi40": "forties/qudsi40.json",
    "shahwaliullah40": "forties/shahwaliullah40.json",
}


def fetch(url: str, retries: int = 4, timeout: int = 120) -> bytes:
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0"})
            with urllib.request.urlopen(req, timeout=timeout) as r:
                return r.read()
        except (urllib.error.URLError, TimeoutError) as e:
            last_err = e
            time.sleep(2 * attempt)
    raise RuntimeError(f"failed after {retries} attempts: {url} ({last_err})")


def count_hadiths(path: Path) -> int:
    with open(path, encoding="utf-8") as f:
        d = json.load(f)
    return len(d.get("hadiths", []))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)
    rows = []
    for slug, rel_path in FILES.items():
        dest = DATA_DIR / f"{slug}.json"
        if args.skip_existing and dest.exists() and dest.stat().st_size > 0:
            status = "skip-existing"
        else:
            url = f"{BASE}/{rel_path}"
            try:
                content = fetch(url)
            except Exception as e:
                print(f"ERRORE {slug}: {e}", file=sys.stderr)
                sys.exit(1)
            dest.write_bytes(content)
            status = "downloaded"

        try:
            n_hadiths = count_hadiths(dest)
        except Exception as e:
            print(f"ERRORE parsing {slug}: {e}", file=sys.stderr)
            sys.exit(1)

        size_mb = dest.stat().st_size / (1024 * 1024)
        rows.append((slug, size_mb, n_hadiths, status))

    print(f"{'fonte':<22} {'MB':>8} {'hadith':>8} {'stato':>14}")
    total_mb = 0.0
    total_hadiths = 0
    for slug, mb, n, status in rows:
        print(f"{slug:<22} {mb:>8.2f} {n:>8} {status:>14}")
        total_mb += mb
        total_hadiths += n
    print(f"{'TOTALE':<22} {total_mb:>8.2f} {total_hadiths:>8}")


if __name__ == "__main__":
    main()
