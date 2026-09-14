"""
Normalizzatore Hadith - data/hadith/*.json -> stesso db/canon.sqlite di
normalize.py, aggiungendo 17 nuovi 'work' (uno per raccolta), senza
toccare i work Tanakh/NT/Corano già presenti (li ricrea se lo schema
non esiste, altrimenti fa solo DELETE mirato sui work hadith per
restare idempotente in caso di ri-lancio).

Mappatura schema:
    work.slug = "hadith_<collection>" (es. hadith_bukhari)
    book = capitolo (chapterId nel JSON sorgente); title_orig = titolo
           arabo del capitolo; per le raccolte senza capitoli reali
           (arba'in) si usa un unico libro fittizio "0".
    verse.chapter = chapterId; verse.verse = idInBook (numero hadith
           nella raccolta, stabile e citabile); verse.text = campo
           'arabic' verbatim (isnad + matn, nessun testo tradotto).

Nessun filtro per grado: la fonte non etichetta sahih/da'if, quindi
tutti gli hadith della raccolta sono inclusi as-is.

Output finale: solo conteggi per raccolta + assert NFC.
"""
import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "hadith"
DB_PATH = ROOT / "db" / "canon.sqlite"

COLLECTIONS = [
    "bukhari", "muslim", "abudawud", "tirmidhi", "nasai", "ibnmajah",
    "malik", "ahmed", "darimi",
    "riyad_assalihin", "shamail_muhammadiyah", "bulugh_almaram",
    "aladab_almufrad", "mishkat_almasabih",
    "nawawi40", "qudsi40", "shahwaliullah40",
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


def wipe_existing_hadith_works(conn: sqlite3.Connection):
    rows = conn.execute(
        "SELECT id FROM work WHERE slug LIKE 'hadith_%'"
    ).fetchall()
    work_ids = [r[0] for r in rows]
    for work_id in work_ids:
        conn.execute(
            "DELETE FROM verse WHERE book_id IN "
            "(SELECT id FROM book WHERE work_id=?)", (work_id,)
        )
        conn.execute("DELETE FROM book WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM work WHERE id=?", (work_id,))


def load_collection(conn: sqlite3.Connection, slug: str):
    path = DATA_DIR / f"{slug}.json"
    if not path.exists():
        print(f"ATTENZIONE hadith: file mancante {slug}", file=sys.stderr)
        return 0

    with open(path, encoding="utf-8") as f:
        data = json.load(f)

    title_ar = data.get("metadata", {}).get("arabic", {}).get("title") or slug
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO work(slug,title,language,direction) VALUES (?,?,?,?)",
        (f"hadith_{slug}", title_ar, "ar", "rtl"),
    )
    work_id = cur.lastrowid

    chapters = {c["id"]: c for c in data.get("chapters", [])}
    book_id_by_chapter = {}

    def get_book_id(chapter_id):
        if chapter_id in book_id_by_chapter:
            return book_id_by_chapter[chapter_id]
        chap = chapters.get(chapter_id)
        title_orig = nfc(chap["arabic"]) if chap and chap.get("arabic") else f"({chapter_id})"
        cur.execute(
            "INSERT INTO book(work_id,code,title_orig,ord) VALUES (?,?,?,?)",
            (work_id, str(chapter_id), title_orig or f"({chapter_id})", chapter_id),
        )
        bid = cur.lastrowid
        book_id_by_chapter[chapter_id] = bid
        return bid

    total = 0
    for h in data.get("hadiths", []):
        chapter_id = h.get("chapterId")
        if chapter_id is None:
            chapter_id = 0
        book_id = get_book_id(chapter_id)
        text = nfc(h.get("arabic", "")).strip()
        if not text:
            continue
        id_in_book = h.get("idInBook", h.get("id", 0))
        cur.execute(
            "INSERT INTO verse(book_id,chapter,verse,text) VALUES (?,?,?,?)",
            (book_id, chapter_id, id_in_book, text),
        )
        total += 1

    return total


def assert_nfc_hadith(conn):
    cur = conn.execute(
        "SELECT v.text FROM verse v JOIN book b ON b.id=v.book_id "
        "JOIN work w ON w.id=b.work_id WHERE w.slug LIKE 'hadith_%'"
    )
    bad = 0
    checked = 0
    for (text,) in cur:
        checked += 1
        if text != unicodedata.normalize("NFC", text):
            bad += 1
    assert bad == 0, f"{bad}/{checked} hadith non in NFC"
    return checked


def main():
    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    wipe_existing_hadith_works(conn)

    counts = {}
    for slug in COLLECTIONS:
        counts[slug] = load_collection(conn, slug)
    conn.commit()

    checked = assert_nfc_hadith(conn)

    print(f"{'collection':<22} {'hadith':>8}")
    total = 0
    for slug in COLLECTIONS:
        n = counts[slug]
        print(f"{slug:<22} {n:>8}")
        total += n
    print(f"{'TOTALE':<22} {total:>8}")
    print(f"PASS nfc_check_hadith: {checked} hadith, 0 non-NFC")

    conn.close()


if __name__ == "__main__":
    main()
