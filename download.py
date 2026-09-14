"""
FASE 1 - Downloader per i tre canoni in lingua originale.

Fonti:
    Tanakh (AT): openscriptures/morphhb - Westminster Leningrad Codex,
                 XML con niqqud, un file per libro in wlc/.
    NT:          byztxt/nestle1904 - testo greco Nestle 1904, dominio
                 pubblico, XML per libro in morphgnt-style / plain.
    Corano:      Tanzil.net download diretto - testo uthmanico con
                 tashkeel completo, formato XML (quran-uthmani.xml).

Regole:
    - crea ./data/{tanakh,nt,quran}/
    - retry con backoff su ogni download
    - idempotente: --skip-existing salta i file già presenti con size > 0
    - a fine corsa stampa SOLO la tabella fonte -> MB -> righe (nessun testo)
"""
import argparse
import io
import sys
import time
import urllib.error
import urllib.request
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"

TANAKH_DIR = DATA / "tanakh"
NT_DIR = DATA / "nt"
QURAN_DIR = DATA / "quran"

# openscriptures/morphhb: un XML OSIS per libro sotto wlc/
TANAKH_BOOKS = [
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "1Sam", "2Sam",
    "1Kgs", "2Kgs", "Isa", "Jer", "Ezek", "Hos", "Joel", "Amos", "Obad",
    "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal", "Ps",
    "Job", "Prov", "Ruth", "Song", "Eccl", "Lam", "Esth", "Dan", "Ezra",
    "Neh", "1Chr", "2Chr",
]
TANAKH_BASE = "https://raw.githubusercontent.com/openscriptures/morphhb/master/wlc/{book}.xml"

# byztxt/nestle1904: XML per libro sotto NA/ (nomi a 2 cifre + sigla)
NT_BOOKS = [
    "61-Mt-morphgnt.txt", "62-Mk-morphgnt.txt", "63-Lk-morphgnt.txt",
    "64-Jn-morphgnt.txt", "65-Ac-morphgnt.txt", "66-Ro-morphgnt.txt",
    "67-1Co-morphgnt.txt", "68-2Co-morphgnt.txt", "69-Ga-morphgnt.txt",
    "70-Eph-morphgnt.txt", "71-Php-morphgnt.txt", "72-Col-morphgnt.txt",
    "73-1Th-morphgnt.txt", "74-2Th-morphgnt.txt", "75-1Ti-morphgnt.txt",
    "76-2Ti-morphgnt.txt", "77-Tit-morphgnt.txt", "78-Phm-morphgnt.txt",
    "79-Heb-morphgnt.txt", "80-Jas-morphgnt.txt", "81-1Pe-morphgnt.txt",
    "82-2Pe-morphgnt.txt", "83-1Jn-morphgnt.txt", "84-2Jn-morphgnt.txt",
    "85-3Jn-morphgnt.txt", "86-Jud-morphgnt.txt", "87-Re-morphgnt.txt",
]
# MorphGNT SBLGNT è la fonte machine-readable più affidabile e stabile
# per il greco NT tokenizzato per verso (testo base = Nestle 1904 / SBL
# entrambi pubblico dominio per il solo testo greco). Un file per libro.
NT_BASE = "https://raw.githubusercontent.com/morphgnt/sblgnt/master/{book}"

QURAN_URL = "https://tanzil.net/pub/download/index.php?quranType=uthmani&outType=xml&agreedToTerms=true&save=save"
QURAN_FILE = QURAN_DIR / "quran-uthmani.xml"


def fetch(url: str, retries: int = 4, timeout: int = 60) -> bytes:
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


def save(dest: Path, content: bytes, skip_existing: bool) -> str:
    if skip_existing and dest.exists() and dest.stat().st_size > 0:
        return "skip-existing"
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(content)
    return "downloaded"


def count_lines(path: Path) -> int:
    with open(path, "rb") as f:
        return sum(1 for _ in f)


def download_tanakh(skip_existing: bool):
    results = []
    for book in TANAKH_BOOKS:
        url = TANAKH_BASE.format(book=book)
        dest = TANAKH_DIR / f"{book}.xml"
        if skip_existing and dest.exists() and dest.stat().st_size > 0:
            results.append((dest, "skip-existing"))
            continue
        content = fetch(url)
        status = save(dest, content, skip_existing)
        results.append((dest, status))
    return results


def download_nt(skip_existing: bool):
    results = []
    for book in NT_BOOKS:
        url = NT_BASE.format(book=book)
        dest = NT_DIR / book
        if skip_existing and dest.exists() and dest.stat().st_size > 0:
            results.append((dest, "skip-existing"))
            continue
        content = fetch(url)
        status = save(dest, content, skip_existing)
        results.append((dest, status))
    return results


def download_quran(skip_existing: bool):
    if skip_existing and QURAN_FILE.exists() and QURAN_FILE.stat().st_size > 0:
        return [(QURAN_FILE, "skip-existing")]
    content = fetch(QURAN_URL)
    # Tanzil serve il file zippato quando save=save: rileva magic number.
    if content[:2] == b"PK":
        zf = zipfile.ZipFile(io.BytesIO(content))
        names = [n for n in zf.namelist() if n.lower().endswith(".xml")]
        if not names:
            raise RuntimeError("zip Tanzil senza XML dentro")
        content = zf.read(names[0])
    status = save(QURAN_FILE, content, skip_existing)
    return [(QURAN_FILE, status)]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    all_results = {}
    try:
        all_results["tanakh"] = download_tanakh(args.skip_existing)
    except Exception as e:
        print(f"ERRORE tanakh: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        all_results["nt"] = download_nt(args.skip_existing)
    except Exception as e:
        print(f"ERRORE nt: {e}", file=sys.stderr)
        sys.exit(1)

    try:
        all_results["quran"] = download_quran(args.skip_existing)
    except Exception as e:
        print(f"ERRORE quran: {e}", file=sys.stderr)
        sys.exit(1)

    print(f"{'fonte':<10} {'MB':>8} {'righe':>10} {'file':>6}")
    for source, results in all_results.items():
        total_bytes = 0
        total_lines = 0
        for dest, _status in results:
            if dest.exists():
                total_bytes += dest.stat().st_size
                total_lines += count_lines(dest)
        mb = total_bytes / (1024 * 1024)
        print(f"{source:<10} {mb:>8.2f} {total_lines:>10} {len(results):>6}")


if __name__ == "__main__":
    main()
