"""
FASE 2 - Normalizzatori: data/{tanakh,nt,quran} -> db/canon.sqlite

Schema:
    work(id, slug, title, language, direction)
    book(id, work_id, code, title_orig, ord)
    verse(id, book_id, chapter, verse, text)

Output finale: SOLO conteggi (SELECT work,COUNT(*) GROUP BY work) e
controlli PASS/FAIL contro totali canonici noti. Nessun testo stampato.
"""
import re
import sqlite3
import sys
import unicodedata
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA = ROOT / "data"
DB_PATH = ROOT / "db" / "canon.sqlite"

TANAKH_BOOKS = [
    "Gen", "Exod", "Lev", "Num", "Deut", "Josh", "Judg", "1Sam", "2Sam",
    "1Kgs", "2Kgs", "Isa", "Jer", "Ezek", "Hos", "Joel", "Amos", "Obad",
    "Jonah", "Mic", "Nah", "Hab", "Zeph", "Hag", "Zech", "Mal", "Ps",
    "Job", "Prov", "Ruth", "Song", "Eccl", "Lam", "Esth", "Dan", "Ezra",
    "Neh", "1Chr", "2Chr",
]
TANAKH_TITLES = {
    "Gen": "בראשית", "Exod": "שמות", "Lev": "ויקרא", "Num": "במדבר",
    "Deut": "דברים", "Josh": "יהושע", "Judg": "שופטים", "1Sam": "שמואל א",
    "2Sam": "שמואל ב", "1Kgs": "מלכים א", "2Kgs": "מלכים ב", "Isa": "ישעיהו",
    "Jer": "ירמיהו", "Ezek": "יחזקאל", "Hos": "הושע", "Joel": "יואל",
    "Amos": "עמוס", "Obad": "עבדיה", "Jonah": "יונה", "Mic": "מיכה",
    "Nah": "נחום", "Hab": "חבקוק", "Zeph": "צפניה", "Hag": "חגי",
    "Zech": "זכריה", "Mal": "מלאכי", "Ps": "תהלים", "Job": "איוב",
    "Prov": "משלי", "Ruth": "רות", "Song": "שיר השירים", "Eccl": "קהלת",
    "Lam": "איכה", "Esth": "אסתר", "Dan": "דניאל", "Ezra": "עזרא",
    "Neh": "נחמיה", "1Chr": "דברי הימים א", "2Chr": "דברי הימים ב",
}

NT_FILES = [
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
NT_CODES = [f.split("-")[1] for f in NT_FILES]
NT_TITLES = {
    "Mt": "ΚΑΤΑ ΜΑΘΘΑΙΟΝ", "Mk": "ΚΑΤΑ ΜΑΡΚΟΝ", "Lk": "ΚΑΤΑ ΛΟΥΚΑΝ",
    "Jn": "ΚΑΤΑ ΙΩΑΝΝΗΝ", "Ac": "ΠΡΑΞΕΙΣ ΑΠΟΣΤΟΛΩΝ", "Ro": "ΠΡΟΣ ΡΩΜΑΙΟΥΣ",
    "1Co": "ΠΡΟΣ ΚΟΡΙΝΘΙΟΥΣ Α", "2Co": "ΠΡΟΣ ΚΟΡΙΝΘΙΟΥΣ Β",
    "Ga": "ΠΡΟΣ ΓΑΛΑΤΑΣ", "Eph": "ΠΡΟΣ ΕΦΕΣΙΟΥΣ",
    "Php": "ΠΡΟΣ ΦΙΛΙΠΠΗΣΙΟΥΣ", "Col": "ΠΡΟΣ ΚΟΛΟΣΣΑΕΙΣ",
    "1Th": "ΠΡΟΣ ΘΕΣΣΑΛΟΝΙΚΕΙΣ Α", "2Th": "ΠΡΟΣ ΘΕΣΣΑΛΟΝΙΚΕΙΣ Β",
    "1Ti": "ΠΡΟΣ ΤΙΜΟΘΕΟΝ Α", "2Ti": "ΠΡΟΣ ΤΙΜΟΘΕΟΝ Β", "Tit": "ΠΡΟΣ ΤΙΤΟΝ",
    "Phm": "ΠΡΟΣ ΦΙΛΗΜΟΝΑ", "Heb": "ΠΡΟΣ ΕΒΡΑΙΟΥΣ", "Jas": "ΙΑΚΩΒΟΥ",
    "1Pe": "ΠΕΤΡΟΥ Α", "2Pe": "ΠΕΤΡΟΥ Β", "1Jn": "ΙΩΑΝΝΟΥ Α",
    "2Jn": "ΙΩΑΝΝΟΥ Β", "3Jn": "ΙΩΑΝΝΟΥ Γ", "Jud": "ΙΟΥΔΑ",
    "Re": "ΑΠΟΚΑΛΥΨΙΣ ΙΩΑΝΝΟΥ",
}

QURAN_EXPECTED_AYAT = 6236
TANAKH_EXPECTED_VERSES = 23213
NT_EXPECTED_VERSES = 7959


def nfc(s: str) -> str:
    return unicodedata.normalize("NFC", s or "")


def strip_ns(tag: str) -> str:
    return tag.split("}")[-1] if "}" in tag else tag


def parse_tanakh_book(path: Path):
    """OSIS container-style verses: <verse osisID="Book.C.V"> contiene
    direttamente elementi <w> (parola), <seg> (es. sof-pasuq, testo di
    punteggiatura) e talvolta <note> (variante/apparato, saltata)."""
    tree = ET.parse(path)
    root = tree.getroot()
    records = []

    for verse_el in root.iter():
        if strip_ns(verse_el.tag) != "verse":
            continue
        osis_id = verse_el.get("osisID", "")
        parts = osis_id.split(".")
        if len(parts) != 3:
            continue
        try:
            chap_num = int(parts[1])
            verse_num = int(parts[2])
        except ValueError:
            continue

        pieces = []

        def collect(el):
            tag = strip_ns(el.tag)
            if tag == "note":
                return
            if tag in ("w", "seg") and el.text:
                pieces.append(el.text)
            for child in el:
                collect(child)
                if child.tail and strip_ns(child.tag) != "note":
                    pieces.append(child.tail)

        for child in verse_el:
            collect(child)
            if child.tail and strip_ns(child.tag) != "note":
                pieces.append(child.tail)

        text = nfc(" ".join(p.strip() for p in pieces if p.strip())).strip()
        if text:
            records.append((chap_num, verse_num, text))
    return records


def parse_nt_book(path: Path):
    """MorphGNT format, one token per line, whitespace-separated fields:
    ref(bbccvv) pos parse-code text word normalized lemma.
    ref = 2-digit book id + 2-digit chapter + 2-digit verse."""
    verses = {}
    order = []
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.rstrip("\n")
            if not line.strip():
                continue
            fields = line.split()
            if len(fields) < 4:
                continue
            ref = fields[0]
            text = fields[3]
            if not ref.isdigit() or len(ref) < 6:
                continue
            chap = int(ref[2:4])
            vers = int(ref[4:6])
            key = (chap, vers)
            if key not in verses:
                verses[key] = []
                order.append(key)
            verses[key].append(text)
    records = []
    for key in order:
        chap, vers = key
        text = nfc(" ".join(verses[key])).strip()
        if text:
            records.append((chap, vers, text))
    return records


def parse_quran(path: Path):
    tree = ET.parse(path)
    root = tree.getroot()
    suras = []
    for sura_el in root:
        if strip_ns(sura_el.tag) != "sura":
            continue
        idx = int(sura_el.get("index"))
        name = sura_el.get("name", "")
        ayat = []
        for aya_el in sura_el:
            if strip_ns(aya_el.tag) != "aya":
                continue
            a_idx = int(aya_el.get("index"))
            text = nfc(aya_el.get("text", "")).strip()
            if text:
                ayat.append((a_idx, text))
        suras.append((idx, name, ayat))
    return suras


def init_db(conn: sqlite3.Connection):
    conn.executescript("""
        DROP TABLE IF EXISTS verse;
        DROP TABLE IF EXISTS book;
        DROP TABLE IF EXISTS work;
        CREATE TABLE work (
            id INTEGER PRIMARY KEY,
            slug TEXT UNIQUE NOT NULL,
            title TEXT NOT NULL,
            language TEXT NOT NULL,
            direction TEXT NOT NULL CHECK(direction IN ('rtl','ltr'))
        );
        CREATE TABLE book (
            id INTEGER PRIMARY KEY,
            work_id INTEGER NOT NULL REFERENCES work(id),
            code TEXT NOT NULL,
            title_orig TEXT NOT NULL,
            ord INTEGER NOT NULL
        );
        CREATE TABLE verse (
            id INTEGER PRIMARY KEY,
            book_id INTEGER NOT NULL REFERENCES book(id),
            chapter INTEGER NOT NULL,
            verse INTEGER NOT NULL,
            text TEXT NOT NULL
        );
        CREATE INDEX idx_verse_book ON verse(book_id);
    """)


def load_tanakh(conn):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO work(slug,title,language,direction) VALUES (?,?,?,?)",
        ("tanakh", "Tanakh (WLC)", "hbo", "rtl"),
    )
    work_id = cur.lastrowid
    total = 0
    missing = []
    for i, code in enumerate(TANAKH_BOOKS):
        path = DATA / "tanakh" / f"{code}.xml"
        if not path.exists():
            missing.append(code)
            continue
        cur.execute(
            "INSERT INTO book(work_id,code,title_orig,ord) VALUES (?,?,?,?)",
            (work_id, code, TANAKH_TITLES[code], i),
        )
        book_id = cur.lastrowid
        records = parse_tanakh_book(path)
        cur.executemany(
            "INSERT INTO verse(book_id,chapter,verse,text) VALUES (?,?,?,?)",
            [(book_id, c, v, t) for c, v, t in records],
        )
        total += len(records)
    if missing:
        print(f"ATTENZIONE tanakh: file mancanti {missing}", file=sys.stderr)
    return total


def load_nt(conn):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO work(slug,title,language,direction) VALUES (?,?,?,?)",
        ("nt", "New Testament (MorphGNT/SBLGNT)", "grc", "ltr"),
    )
    work_id = cur.lastrowid
    total = 0
    missing = []
    for i, (fname, code) in enumerate(zip(NT_FILES, NT_CODES)):
        path = DATA / "nt" / fname
        if not path.exists():
            missing.append(fname)
            continue
        cur.execute(
            "INSERT INTO book(work_id,code,title_orig,ord) VALUES (?,?,?,?)",
            (work_id, code, NT_TITLES[code], i),
        )
        book_id = cur.lastrowid
        records = parse_nt_book(path)
        cur.executemany(
            "INSERT INTO verse(book_id,chapter,verse,text) VALUES (?,?,?,?)",
            [(book_id, c, v, t) for c, v, t in records],
        )
        total += len(records)
    if missing:
        print(f"ATTENZIONE nt: file mancanti {missing}", file=sys.stderr)
    return total


def load_quran(conn):
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO work(slug,title,language,direction) VALUES (?,?,?,?)",
        ("quran", "Quran (Tanzil Uthmani)", "ar", "rtl"),
    )
    work_id = cur.lastrowid
    path = DATA / "quran" / "quran-uthmani.xml"
    if not path.exists():
        print("ERRORE quran: file mancante", file=sys.stderr)
        return 0
    suras = parse_quran(path)
    total = 0
    for i, (idx, name, ayat) in enumerate(suras):
        cur.execute(
            "INSERT INTO book(work_id,code,title_orig,ord) VALUES (?,?,?,?)",
            (work_id, str(idx), name, i),
        )
        book_id = cur.lastrowid
        cur.executemany(
            "INSERT INTO verse(book_id,chapter,verse,text) VALUES (?,?,?,?)",
            [(book_id, idx, a_idx, t) for a_idx, t in ayat],
        )
        total += len(ayat)
    return total


def assert_nfc(conn):
    cur = conn.execute("SELECT text FROM verse")
    bad = 0
    checked = 0
    for (text,) in cur:
        checked += 1
        if text != unicodedata.normalize("NFC", text):
            bad += 1
    assert bad == 0, f"{bad}/{checked} verse non in NFC"
    return checked


def main():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    if DB_PATH.exists():
        DB_PATH.unlink()
    conn = sqlite3.connect(DB_PATH)
    init_db(conn)

    tanakh_total = load_tanakh(conn)
    nt_total = load_nt(conn)
    quran_total = load_quran(conn)
    conn.commit()

    checked = assert_nfc(conn)

    print(f"{'work':<10} {'count':>8}")
    for row in conn.execute(
        "SELECT w.slug, COUNT(*) FROM verse v "
        "JOIN book b ON b.id=v.book_id JOIN work w ON w.id=b.work_id "
        "GROUP BY w.slug ORDER BY w.slug"
    ):
        print(f"{row[0]:<10} {row[1]:>8}")

    def check(name, actual, expected, tol):
        diff = abs(actual - expected)
        status = "PASS" if diff <= tol else "FAIL"
        print(f"{status} {name}: actual={actual} expected={expected} diff={diff}")

    check("quran_ayat", quran_total, QURAN_EXPECTED_AYAT, 0)
    check("tanakh_verses", tanakh_total, TANAKH_EXPECTED_VERSES, 100)
    check("nt_verses", nt_total, NT_EXPECTED_VERSES, 50)
    print(f"PASS nfc_check: {checked} verses, 0 non-NFC")

    conn.close()


if __name__ == "__main__":
    main()
