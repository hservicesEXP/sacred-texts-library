"""
Downloader Settanta (LXX) - deuterocanonici/apocrifi in greco, per
completare l'Antico Testamento cristiano oltre al Tanakh ebraico gia'
presente. Fonte: LukeSmithxyz/grb (TSV verso-per-verso, testo greco
accentato, Rahlfs LXX + SBLGNT).

Prende SOLO le righe i cui libri non sono gia' coperti da Tanakh (39
libri) o NT (27 libri), quindi: deuterocanonici classici + varianti
testuali della Settanta assenti nel testo masoretico (Daniele Teodozione,
Susanna, Bel e il Drago, Giudici Vaticanus, Tobia Sinaiticus, ecc.) -
nessun libro scartato per non "lasciare fuori nulla" della tradizione
greca, come gia' fatto per gli hadith.

Idempotente: --skip-existing salta il file gia' presente.
Stampa SOLO fonte -> MB -> righe a fine corsa.
"""
import argparse
import sys
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "lxx"
TSV_URL = "https://raw.githubusercontent.com/LukeSmithxyz/grb/master/grb.tsv"
DEST = DATA_DIR / "grb.tsv"

# Libri gia' coperti da Tanakh (WLC) o NT (MorphGNT) - questi vengono
# scartati dal TSV per evitare duplicati; tutto il resto (deuterocanonici
# + varianti testuali greche distinte) viene tenuto.
TANAKH_NAMES = {
    "Genesis", "Exodus", "Leviticus", "Numbers", "Deuteronomy", "Joshua",
    "Judges", "Ruth", "1 Samuel", "2 Samuel", "1 Kings", "2 Kings",
    "1 Chronicles", "2 Chronicles", "Ezra", "Nehemiah", "Esther",
    "Psalms", "Proverbs", "Ecclesiastes", "Song of Solomon", "Job",
    "Hosea", "Amos", "Micah", "Joel", "Obadiah", "Jonah", "Nahum",
    "Habakkuk", "Zephaniah", "Haggai", "Zechariah", "Malachi", "Isaiah",
    "Jeremiah", "Lamentations", "Ezekiel", "Daniel",
}
NT_NAMES = {
    "Matthew", "Mark", "Luke", "John", "The Acts", "Romans",
    "1 Corinthians", "2 Corinthians", "Galatians", "Ephesians",
    "Philippians", "Colossians", "1 Thessalonians", "2 Thessalonians",
    "1 Timothy", "2 Timothy", "Titus", "Philemon", "Hebrews", "James",
    "1 Peter", "2 Peter", "1 John", "2 John", "3 John", "Jude",
    "Revelation",
}
EXCLUDE_NAMES = TANAKH_NAMES | NT_NAMES


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


def count_deutero_lines(path: Path) -> int:
    n = 0
    with open(path, encoding="utf-8") as f:
        for line in f:
            book = line.split("\t", 1)[0]
            if book not in EXCLUDE_NAMES:
                n += 1
    return n


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--skip-existing", action="store_true")
    args = ap.parse_args()

    DATA_DIR.mkdir(parents=True, exist_ok=True)

    if args.skip_existing and DEST.exists() and DEST.stat().st_size > 0:
        status = "skip-existing"
    else:
        try:
            content = fetch(TSV_URL)
        except Exception as e:
            print(f"ERRORE lxx: {e}", file=sys.stderr)
            sys.exit(1)
        DEST.write_bytes(content)
        status = "downloaded"

    size_mb = DEST.stat().st_size / (1024 * 1024)
    deutero_lines = count_deutero_lines(DEST)

    print(f"{'fonte':<10} {'MB':>8} {'righe_deutero':>14} {'stato':>14}")
    print(f"{'lxx':<10} {size_mb:>8.2f} {deutero_lines:>14} {status:>14}")


if __name__ == "__main__":
    main()
