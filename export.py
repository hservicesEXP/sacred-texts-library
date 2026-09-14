"""
FASE 3a - Indice FTS5 (detail=none) + export XHTML per libro, stampa-pronto.

Uso:
    python export.py --index          # crea/ricrea indice FTS5 su db/canon.sqlite
    python export.py --xhtml          # esporta tutti i libri in ./export/<work>/<code>.xhtml
    python export.py --index --xhtml  # entrambi

Font dichiarati in CSS (non incorporati, solo font-family con fallback):
    ebraico: 'Ezra SIL', 'Noto Serif Hebrew', serif
    arabo:   'KFGQPC Uthmanic HAFS', 'Noto Naskh Arabic', serif
    greco:   'Gentium Plus', serif

Nessun testo stampato in console: solo conteggi.
"""
import argparse
import html
import sqlite3
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "db" / "canon.sqlite"
EXPORT_DIR = ROOT / "docs"

FONT_STACKS = {
    "hbo": "'Ezra SIL', 'Noto Serif Hebrew', serif",
    "ar": "'KFGQPC Uthmanic HAFS', 'Noto Naskh Arabic', serif",
    "grc": "'Gentium Plus', serif",
}

CSS_TEMPLATE = """
@page {{ margin: 2cm; }}
body {{
    font-family: {font_stack};
    direction: {direction};
    unicode-bidi: isolate;
    font-size: 16pt;
    line-height: 1.9;
    max-width: 46em;
    margin: 0 auto;
    padding: 1.5em;
}}
h1 {{ text-align: center; font-size: 1.4em; margin-bottom: 1.2em; }}
p.verse {{ margin: 0 0 0.6em 0; }}
span.vnum {{
    font-family: sans-serif;
    font-size: 0.6em;
    color: #888;
    unicode-bidi: isolate;
    margin: 0 0.4em;
}}
"""


def build_fts5_index(conn: sqlite3.Connection) -> int:
    conn.executescript("DROP TABLE IF EXISTS verse_fts;")
    conn.execute(
        "CREATE VIRTUAL TABLE verse_fts USING fts5("
        "text, content='verse', content_rowid='id', detail=none"
        ")"
    )
    conn.execute(
        "INSERT INTO verse_fts(rowid, text) SELECT id, text FROM verse"
    )
    conn.commit()
    return conn.execute("SELECT COUNT(*) FROM verse_fts").fetchone()[0]


def export_book(conn, work_slug, work_language, direction, book_code, book_title, book_id):
    out_dir = EXPORT_DIR / work_slug
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{book_code}.xhtml"

    font_stack = FONT_STACKS.get(work_language, "serif")
    css = CSS_TEMPLATE.format(font_stack=font_stack, direction=direction)

    rows = conn.execute(
        "SELECT chapter, verse, text FROM verse WHERE book_id=? "
        "ORDER BY chapter, verse",
        (book_id,),
    ).fetchall()

    parts = [
        '<?xml version="1.0" encoding="UTF-8"?>',
        '<!DOCTYPE html>',
        f'<html xmlns="http://www.w3.org/1999/xhtml" lang="{html.escape(work_language)}" dir="{direction}">',
        '<head>',
        '<meta charset="UTF-8" />',
        f'<title>{html.escape(book_title)}</title>',
        f'<style>{css}</style>',
        '</head>',
        '<body>',
        f'<h1>{html.escape(book_title)}</h1>',
    ]

    current_chapter = None
    for chapter, verse, text in rows:
        if chapter != current_chapter:
            if current_chapter is not None:
                parts.append('<hr/>')
            current_chapter = chapter
            parts.append(f'<h2 class="chapter">{chapter}</h2>')
        esc_text = html.escape(text)
        parts.append(
            f'<p class="verse"><span class="vnum">{verse}</span>{esc_text}</p>'
        )

    parts.append('</body></html>')
    out_path.write_text("\n".join(parts), encoding="utf-8")
    return len(rows), out_path


def export_all(conn):
    counts = {}
    for work_id, slug, language, direction in conn.execute(
        "SELECT id, slug, language, direction FROM work ORDER BY slug"
    ):
        total_verses = 0
        total_books = 0
        for book_id, code, title_orig in conn.execute(
            "SELECT id, code, title_orig FROM book WHERE work_id=? ORDER BY ord",
            (work_id,),
        ):
            n, _path = export_book(conn, slug, language, direction, code, title_orig, book_id)
            total_verses += n
            total_books += 1
        counts[slug] = (total_books, total_verses)
    return counts


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--index", action="store_true")
    ap.add_argument("--xhtml", action="store_true")
    args = ap.parse_args()

    if not args.index and not args.xhtml:
        ap.error("specifica almeno --index o --xhtml")

    conn = sqlite3.connect(DB_PATH)

    if args.index:
        n = build_fts5_index(conn)
        print(f"fts5_rows {n}")

    if args.xhtml:
        counts = export_all(conn)
        print(f"{'work':<10} {'books':>6} {'verses':>8}")
        for slug, (books, verses) in sorted(counts.items()):
            print(f"{slug:<10} {books:>6} {verses:>8}")

    conn.close()


if __name__ == "__main__":
    main()
