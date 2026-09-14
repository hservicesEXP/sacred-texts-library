# Sacred Texts Library — Quran V1

Quran-only release of the project.

Included:
- All 114 surahs / 6,236 ayat from the supplied Tanzil Uthmani XML.
- Deterministic local search by Arabic text, reference, morphology root and lemma.
- Surah navigation and direct verse links.
- Word-level morphology panel (POS, lemma, root, source features).
- Local bookmarks and notes via localStorage.
- Arabic RTL mobile-first reader.
- Device speech synthesis via Web Speech API.
- PWA manifest and service worker with runtime caching.
- Optional cinematic 3D-style entrance, skip control and reduced-motion handling.
- Custodian, Scholar, Cartographer and Codicologist roles.
- Source/licensing/methodology page.

Run:
    python3 -m http.server 8080 --directory docs
Open http://127.0.0.1:8080/

The Hadith, Tanakh, New Testament and Talmud datasets are not included in this release.
