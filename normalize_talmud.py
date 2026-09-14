"""
Normalizzatore Talmud Bavli (ebraico/aramaico) - data/talmud_he/*.json
-> canon.sqlite, un work per trattato ("talmud_<Tractate>"), categoria
Ebraismo, ordinato secondo i sei sedarim (Zeraim->Tahorot) subito dopo
il Tanakh.

Schema sorgente Sefaria (verificato nella sessione precedente):
    text[daf_index][line_index] = stringa ebraica/aramaica
    sectionNames == ["Daf", "Line"]
    daf_index 0 -> "1a" (placeholder senza testo reale), il primo
    contenuto e' sempre a partire da index>=2 -> "2a".

Mappatura verse:
    verse.chapter = numero daf (es. 2 per "2a")
    verse.verse   = codifica amud+riga: amud 'a' -> line, amud 'b' ->
                    line + 1000 (offset arbitrario per tenere gli amudim
                    distinti pur restando dentro una singola tabella
                    chapter/verse; la pagina esportata mostra comunque
                    "daf amud:riga" leggibile, vedi export_talmud.py se
                    servisse un formato dedicato - qui riuso lo schema
                    generico per coerenza con gli altri canoni).
    book = trattato stesso (un solo "libro" per lavoro, code="1")

Nessun filtro di contenuto: ogni riga con testo ebraico non vuoto viene
inclusa cosi' com'e', niqqud preservato, NFC applicato.

Output finale: solo conteggi per trattato + assert NFC.
"""
import json
import sqlite3
import sys
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DATA_DIR = ROOT / "data" / "talmud_he"
MANIFEST_PATH = ROOT / "data" / "talmud_he_manifest.json"
DB_PATH = ROOT / "db" / "canon.sqlite"

AMUD_B_OFFSET = 1000


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


def wipe_existing_talmud_works(conn: sqlite3.Connection):
    rows = conn.execute("SELECT id FROM work WHERE slug LIKE 'talmud_%'").fetchall()
    for (work_id,) in rows:
        conn.execute(
            "DELETE FROM verse WHERE book_id IN (SELECT id FROM book WHERE work_id=?)",
            (work_id,),
        )
        conn.execute("DELETE FROM book WHERE work_id=?", (work_id,))
        conn.execute("DELETE FROM work WHERE id=?", (work_id,))


def daf_amud_offset(index: int):
    """index 0 -> daf 1 amud a, index 1 -> daf 1 amud b, index 2 -> daf 2
    amud a, ... (verificato empiricamente nella sessione precedente)."""
    daf = 1 + index // 2
    is_b = index % 2 == 1
    return daf, is_b


def load_collection(conn: sqlite3.Connection, tractate: str, order: int):
    path = DATA_DIR / f"{tractate}.json"
    if not path.exists():
        print(f"ATTENZIONE talmud: file mancante {tractate}", file=sys.stderr)
        return 0

    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    text = data.get("text", [])

    cur = conn.cursor()
    cur.execute(
        "INSERT INTO work(slug,title,language,direction) VALUES (?,?,?,?)",
        (f"talmud_{tractate}", tractate, "arc", "rtl"),
    )
    work_id = cur.lastrowid
    cur.execute(
        "INSERT INTO book(work_id,code,title_orig,ord) VALUES (?,?,?,?)",
        (work_id, "1", tractate, 0),
    )
    book_id = cur.lastrowid

    total = 0
    for daf_index, lines in enumerate(text):
        if not lines:
            continue
        daf, is_b = daf_amud_offset(daf_index)
        for line_idx, line_text in enumerate(lines):
            t = nfc(line_text).strip()
            if not t:
                continue
            verse_num = (line_idx + 1) + (AMUD_B_OFFSET if is_b else 0)
            cur.execute(
                "INSERT INTO verse(book_id,chapter,verse,text) VALUES (?,?,?,?)",
                (book_id, daf, verse_num, t),
            )
            total += 1
    return total


def main():
    if not MANIFEST_PATH.exists():
        print("ERRORE: data/talmud_he_manifest.json mancante, lancia prima download_talmud.py", file=sys.stderr)
        sys.exit(1)
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8"))
    tractates = sorted(manifest.keys(), key=lambda t: manifest[t]["order"])

    conn = sqlite3.connect(DB_PATH)
    ensure_schema(conn)
    wipe_existing_talmud_works(conn)

    counts = {}
    for i, tractate in enumerate(tractates):
        counts[tractate] = load_collection(conn, tractate, i)
    conn.commit()

    cur = conn.execute(
        "SELECT v.text FROM verse v JOIN book b ON b.id=v.book_id "
        "JOIN work w ON w.id=b.work_id WHERE w.slug LIKE 'talmud_%'"
    )
    bad = 0
    checked = 0
    for (t,) in cur:
        checked += 1
        if t != unicodedata.normalize("NFC", t):
            bad += 1
    assert bad == 0, f"{bad}/{checked} righe talmud non in NFC"

    print(f"{'trattato':<20} {'righe':>8}")
    total = 0
    for tractate in tractates:
        n = counts[tractate]
        print(f"{tractate:<20} {n:>8}")
        total += n
    print(f"{'TOTALE':<20} {total:>8}")
    print(f"PASS nfc_check_talmud: {checked} righe, 0 non-NFC")

    conn.close()


if __name__ == "__main__":
    main()
