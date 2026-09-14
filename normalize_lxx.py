"""
Normalizzatore Settanta (LXX) - data/lxx/grb.tsv -> canon.sqlite,
aggiungendo un work "lxx_deutero" (Antico Testamento greco -
deuterocanonici e varianti testuali assenti nel Tanakh masoretico),
categorizzato sotto Cristianesimo.

Un solo work con un libro per ogni nome distinto nel TSV (stesso
raggruppamento fatto dal downloader). Verse.chapter/verse presi
direttamente dalle colonne 3/4 del TSV originale (capitolo, versetto);
la colonna 5 (indice riga interno alla fonte) viene ignorata.

Nessun filtro editoriale oltre l'esclusione dei libri gia' presenti in
Tanakh/NT (fatta a monte dal downloader/qui stesso, per doppia sicurezza).

Output finale: solo conteggi per libro + assert NFC.
"""
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
TSV_PATH = ROOT / "data" / "lxx" / "grb.tsv"
DB_PATH = ROOT / "db" / "canon.sqlite"

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

# Ordine canonico approssimativo (storico/tematico) per navigazione
BOOK_ORDER = [
    "1 Esdras", "2 Esdras", "Tobit", "Tobit (Sinaiticus)", "Judith",
    "1 Maccabees", "2 Maccabees", "3 Maccabees", "4 Maccabees",
    "Odes", "Wisdom of Solomon", "Sirach", "Psalms of Solomon",
    "Baruch", "Letter of Jeremiah", "Sussana", "Sussana (Theodotion)",
    "Daniel (Theodotion)", "Bel and the Dragon",
    "Bel and the Dragon (Theodotion)", "Judges (Vaticanus)",
]


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "")


def ensure_schema(conn: sqlite3.Connection):
    conn.executescript("""
        CREATE TABLE IF NOT EXISTS work (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            language TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('rtl','ltr'))
        );
        CREATE TABLE IF NOT EXISTS book (
            id INTEGER PRIMARY KEY,
            work_id INTEGER NOT NULL REFERENCES work(id),
            code TEXT NOT NULL,
            title_orig TEXT NOT NULL,
            ord INTEGER NOT NULL
        );
        CREATE TABLE IF NOT EXISTS verse (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL REFERENCES book(id),
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            text TEXT NOT NULL
        );
        CREATE INDEX IF NOT EXISTS idx_verse_book ON verse(book_id);
    """)


def wipe_existing(conn: sqlite3.Connection, slug: str):
    row = conn.execute("SELECT id FROM work WHERE slug=?", (slug,)).fetchone()
    if not row:
        return
    work_id = row[0]
    conn.execute(
        "DELETE FROM verse WHERE book_id IN (SELECT id FROM book WHERE work_id=?)",
        (work_id,),
    )
    conn.execute("DELETE FROM book WHERE work_id=?", (work_id,))
    conn.execute("DELETE FROM work WHERE id=?", (work_id,))


def main():
    if not TSV_PATH.exists():
        print("ERRORE: data/lxx/grb.tsv mancante", file=sys.stderr)
        sys.exit(1)

    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    wipe_existing(conn, "lxx_deutero")

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO work(slug,title,language,direction) VALUES (?,?,?,?)",
        ("lxx_deutero", "Settanta - Deuterocanonici e varianti greche (LXX)", "grc", "ltr"),
    )
    work_id = cur.lastrowid

    book_id_by_name = {}
    counts = {}
    seen_unknown = set()

    with open(TSV_PATH, encoding="utf-8") as f:
        for line in f:
            parts = line.rstrip("\n").split("\t")
            if len(parts) != 6:
                continue
            book, abbrev, chap_book_idx, chapter_s, verse_s, text = parts
            if book in EXCLUDE_NAMES:
                continue

            if book not in book_id_by_name:
                if book not in BOOK_ORDER:
                    seen_unknown.add(book)
                ordv = BOOK_ORDER.index(book) if book in BOOK_ORDER else len(BOOK_ORDER) + len(seen_unknown)
                cur.execute(
                    "INSERT INTO book(work_id,code,title_orig,ord) VALUES (?,?,?,?)",
                    (work_id, abbrev, book, ordv),
                )
                book_id_by_name[book] = cur.lastrowid
                counts[book] = 0

            try:
                chapter = int(chapter_s)
                verse = int(verse_s)
            except ValueError:
                continue

            text_nfc = nfc(text).strip()
            if not text_nfc:
                continue

            cur.execute(
                "INSERT INTO verse(book_id,chapter,verse,text) VALUES (?,?,?,?)",
                (book_id_by_name[book], chapter, verse, text_nfc),
            )
            counts[book] += 1

    conn.commit()

    if seen_unknown:
        print(f"ATTENZIONE lxx: libri non previsti in BOOK_ORDER {sorted(seen_unknown)}", file=sys.stderr)

    cur2 = conn.execute(
        "SELECT v.text FROM verse v JOIN book b ON b.id=v.book_id WHERE b.work_id=?",
        (work_id,),
    )
    bad = 0
    checked = 0
    for (text,) in cur2:
        checked += 1
        if text != unicodedata.normalize("NFC", text):
            bad += 1
    assert bad == 0, f"{bad}/{checked} versi lxx non in NFC"

    print(f"{'book':<32} {'verses':>8}")
    total = 0
    for book in sorted(counts, key=lambda b: (BOOK_ORDER.index(b) if b in BOOK_ORDER else 999, b)):
        n = counts[book]
        print(f"{book:<32} {n:>8}")
        total += n
    print(f"{'TOTALE':<32} {total:>8}")
    print(f"PASS nfc_check_lxx: {checked} versi, 0 non-NFC")

    conn.close()


if __name__ == "__main__":
    main()
