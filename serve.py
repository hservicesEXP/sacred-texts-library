"""
FASE 3b - Mini web reader locale: indice organizzato per religione,
con libri in ordine di importanza dentro ogni categoria. Nessuna
dipendenza esterna, solo http.server. Serve staticamente ./export/ e
genera ./export/index.html.

Uso:
    python serve.py --build-index      # rigenera solo l'indice HTML
    python serve.py --port 8765        # genera indice e avvia il server
"""
import argparse
import html
import sqlite3
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ROOT = Path(__file__).resolve().parent
DB_PATH = ROOT / "db" / "canon.sqlite"
EXPORT_DIR = ROOT / "docs"

# Ordine canonico dei sei sedarim (Zeraim->Tahorot) per i 37 trattati
TALMUD_TRACTATES_ORDER = [
    "Berakhot",
    "Beitzah", "Chagigah", "Eruvin", "Megillah", "Moed Katan", "Pesachim",
    "Rosh Hashanah", "Shabbat", "Sukkah", "Taanit", "Yoma",
    "Gittin", "Ketubot", "Kiddushin", "Nazir", "Nedarim", "Sotah", "Yevamot",
    "Avodah Zarah", "Bava Batra", "Bava Kamma", "Bava Metzia", "Horayot",
    "Makkot", "Sanhedrin", "Shevuot",
    "Arakhin", "Bekhorot", "Chullin", "Keritot", "Meilah", "Menachot",
    "Tamid", "Temurah", "Zevachim",
    "Niddah",
]

# Categoria -> (titolo religione/tradizione, [slug work in ordine di importanza])
CATEGORIES = [
    ("Ebraismo", ["tanakh"] + [f"talmud_{t}" for t in TALMUD_TRACTATES_ORDER]),
    ("Cristianesimo", ["tanakh", "lxx_deutero", "nt"]),
    ("Islam", [
        "quran",
        "hadith_bukhari",
        "hadith_muslim",
        "hadith_abudawud",
        "hadith_tirmidhi",
        "hadith_nasai",
        "hadith_ibnmajah",
        "hadith_malik",
        "hadith_ahmed",
        "hadith_darimi",
        "hadith_riyad_assalihin",
        "hadith_mishkat_almasabih",
        "hadith_bulugh_almaram",
        "hadith_aladab_almufrad",
        "hadith_shamail_muhammadiyah",
        "hadith_nawawi40",
        "hadith_qudsi40",
        "hadith_shahwaliullah40",
    ]),
]

# PDF extra non derivati dal DB: categoria -> lista di (titolo, path relativo
# a export/, nota). Il Talmud e' bilingue (originale+traduzione, prodotto
# nella sessione precedente); il Corano italiano e' SOLO traduzione, quindi
# marcato esplicitamente per non confonderlo col testo arabo originale.
EXTRA_PDFS = {
    "Ebraismo": [
        ("Talmud Bavli (Ebraico/Aramaico + Inglese, bilingue)", "pdf/Talmud_Bavli_Bilingual.pdf", "PDF, 37 trattati"),
    ],
    "Islam": [
        ("Corano - traduzione italiana (NON testo originale)", "pdf/corano_italiano.pdf", "PDF, solo traduzione"),
    ],
}

WORK_TITLES_IT = {
    "tanakh": "Tanakh / Antico Testamento (Masoretico, WLC)",
    "lxx_deutero": "Deuterocanonici (Settanta, greco)",
    "nt": "Nuovo Testamento (Greco, MorphGNT/SBLGNT)",
    "quran": "Corano (Uthmanico, Tanzil)",
    "hadith_bukhari": "Sahih al-Bukhari",
    "hadith_muslim": "Sahih Muslim",
    "hadith_abudawud": "Sunan Abi Dawud",
    "hadith_tirmidhi": "Jami' at-Tirmidhi",
    "hadith_nasai": "Sunan an-Nasa'i",
    "hadith_ibnmajah": "Sunan Ibn Majah",
    "hadith_malik": "Muwatta Malik",
    "hadith_ahmed": "Musnad Ahmad",
    "hadith_darimi": "Sunan ad-Darimi",
    "hadith_riyad_assalihin": "Riyad as-Salihin",
    "hadith_shamail_muhammadiyah": "Shamail al-Muhammadiyah",
    "hadith_bulugh_almaram": "Bulugh al-Maram",
    "hadith_aladab_almufrad": "Al-Adab Al-Mufrad",
    "hadith_mishkat_almasabih": "Mishkat al-Masabih",
    "hadith_nawawi40": "Quaranta di an-Nawawi",
    "hadith_qudsi40": "Quaranta Qudsi",
    "hadith_shahwaliullah40": "Quaranta di Shah Waliullah",
}

def work_label(slug: str) -> str:
    if slug in WORK_TITLES_IT:
        return WORK_TITLES_IT[slug]
    if slug.startswith("talmud_"):
        return f"Talmud Bavli - {slug[len('talmud_'):].replace('_', ' ')}"
    return slug


INDEX_CSS = """
body { font-family: sans-serif; max-width: 55em; margin: 2em auto; padding: 0 1em; }
h1 { font-size: 1.6em; }
h2.category { font-size: 1.3em; margin-top: 2em; border-bottom: 2px solid #444; padding-bottom: 0.2em; }
h3.worktitle { font-size: 1.05em; margin: 1em 0 0.3em 0; color: #333; }
ul.books { list-style: none; padding: 0; display: flex; flex-wrap: wrap; gap: 0.5em; margin: 0 0 0.8em 0; }
ul.books a {
    display: block; padding: 0.35em 0.7em; background: #f2f2f2;
    border-radius: 6px; text-decoration: none; color: #222; font-size: 0.85em;
}
ul.books a:hover { background: #e0e0e0; }
ul.pdfs { list-style: none; padding: 0; margin: 0 0 1.2em 0; }
ul.pdfs li { margin: 0.3em 0; }
ul.pdfs a {
    display: inline-block; padding: 0.5em 0.9em; background: #fff3d6;
    border: 1px solid #e0c070; border-radius: 6px; text-decoration: none;
    color: #4a3300; font-size: 0.95em; font-weight: bold;
}
ul.pdfs a:hover { background: #ffe8b0; }
ul.pdfs span.note { font-size: 0.8em; color: #777; margin-left: 0.6em; font-weight: normal; }
"""


def build_index_html(conn) -> int:
    work_rows = {
        slug: (work_id, language, direction)
        for work_id, slug, language, direction in conn.execute(
            "SELECT id, slug, language, direction FROM work"
        )
    }

    parts = [
        "<!DOCTYPE html><html lang='it'><head><meta charset='UTF-8'/>",
        "<title>Libreria testi sacri - lingua originale</title>",
        f"<style>{INDEX_CSS}</style></head><body>",
        "<h1>Libreria digitale - testi sacri in lingua originale</h1>",
        "<p>Nessuna traduzione. Solo testo originale (niqqud, tashkeel, "
        "accenti politonici preservati).</p>",
    ]

    total_books = 0
    known_slugs = set()
    for category_title, slugs in CATEGORIES:
        parts.append(f"<h2 class='category'>{html.escape(category_title)}</h2>")

        for pdf_title, pdf_path, pdf_note in EXTRA_PDFS.get(category_title, []):
            parts.append("<ul class='pdfs'><li>")
            parts.append(
                f"<a href='{html.escape(pdf_path)}'>{html.escape(pdf_title)}</a>"
                f"<span class='note'>{html.escape(pdf_note)}</span>"
            )
            parts.append("</li></ul>")

        for slug in slugs:
            known_slugs.add(slug)
            if slug not in work_rows:
                continue
            work_id, language, direction = work_rows[slug]
            label = work_label(slug)
            parts.append(f"<h3 class='worktitle'>{html.escape(label)}</h3><ul class='books'>")
            for code, title_orig in conn.execute(
                "SELECT code, title_orig FROM book WHERE work_id=? ORDER BY ord",
                (work_id,),
            ):
                href = f"{slug}/{code}.xhtml"
                parts.append(f"<li><a href='{href}'>{html.escape(code)}</a></li>")
                total_books += 1
            parts.append("</ul>")

    # eventuali work non categorizzati esplicitamente (rete di sicurezza)
    leftover = [s for s in work_rows if s not in known_slugs]
    if leftover:
        parts.append("<h2 class='category'>Altro</h2>")
        for slug in sorted(leftover):
            work_id, language, direction = work_rows[slug]
            label = work_label(slug)
            parts.append(f"<h3 class='worktitle'>{html.escape(label)}</h3><ul class='books'>")
            for code, title_orig in conn.execute(
                "SELECT code, title_orig FROM book WHERE work_id=? ORDER BY ord",
                (work_id,),
            ):
                href = f"{slug}/{code}.xhtml"
                parts.append(f"<li><a href='{href}'>{html.escape(code)}</a></li>")
                total_books += 1
            parts.append("</ul>")

    parts.append("</body></html>")

    EXPORT_DIR.mkdir(parents=True, exist_ok=True)
    (EXPORT_DIR / "index.html").write_text("\n".join(parts), encoding="utf-8")
    return total_books


class QuietHandler(SimpleHTTPRequestHandler):
    """SimpleHTTPRequestHandler di base risponde sempre 200 con il file
    intero e ignora l'header Range: molti viewer PDF integrati nel
    browser aprono il documento a colpi di richieste Range e falliscono
    (\"Impossibile caricare il documento\") se ricevono sempre 200 pieno
    invece di 206 Partial Content. Questo handler implementa Range su
    singolo intervallo byte, sufficiente per i lettori PDF standard."""

    def log_message(self, fmt, *args):
        pass

    def send_head(self):
        path = self.translate_path(self.path)
        if not path or not Path(path).is_file():
            return super().send_head()

        range_header = self.headers.get("Range")
        file_size = Path(path).stat().st_size

        if not range_header:
            f = super().send_head()
            if f is not None:
                self.send_header("Accept-Ranges", "bytes")
            return f

        try:
            units, _, range_spec = range_header.partition("=")
            start_s, _, end_s = range_spec.partition("-")
            start = int(start_s) if start_s else 0
            end = int(end_s) if end_s else file_size - 1
            end = min(end, file_size - 1)
            if start > end or units != "bytes":
                raise ValueError
        except ValueError:
            self.send_error(416, "Requested Range Not Satisfiable")
            return None

        f = open(path, "rb")
        f.seek(start)
        length = end - start + 1

        self.send_response(206)
        ctype = self.guess_type(path)
        self.send_header("Content-type", ctype)
        self.send_header("Content-Range", f"bytes {start}-{end}/{file_size}")
        self.send_header("Accept-Ranges", "bytes")
        self.send_header("Content-Length", str(length))
        self.end_headers()

        self._range_remaining = length
        return f

    def copyfile(self, source, outputfile):
        remaining = getattr(self, "_range_remaining", None)
        if remaining is None:
            return super().copyfile(source, outputfile)
        buf_size = 64 * 1024
        while remaining > 0:
            chunk = source.read(min(buf_size, remaining))
            if not chunk:
                break
            outputfile.write(chunk)
            remaining -= len(chunk)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--build-index", action="store_true")
    ap.add_argument("--port", type=int, default=0)
    args = ap.parse_args()

    conn = sqlite3.connect(DB_PATH)
    n = build_index_html(conn)
    conn.close()
    print(f"index_books {n}")

    if args.port:
        import functools
        handler = functools.partial(QuietHandler, directory=str(EXPORT_DIR))
        server = ThreadingHTTPServer(("127.0.0.1", args.port), handler)
        print(f"serving http://127.0.0.1:{args.port}/index.html")
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass


if __name__ == "__main__":
    main()
