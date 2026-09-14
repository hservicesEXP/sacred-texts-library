# Sacred Texts Library — Quran V1 (rebuild)

This package is the rebuilt Quran-only V1 based on the supplied project and corpus.

## Included
- 114 surahs / 6,236 ayat
- Uthmani Arabic text already present in the supplied dataset
- Deterministic browser search by Arabic text, reference, Buckwalter root and lemma
- Arabic normalization for search only
- Small explicit Italian concept index (not a translation)
- Word-level morphology from `data/quranic-corpus-morphology-0.4.txt`
- Reader with RTL, direct verse URLs, navigation, font controls, local bookmarks and notes
- Web Speech API Arabic TTS when available on the device
- PWA/service-worker cache with versioned invalidation and network-first JSON data
- Cinematic gate intro that can be skipped and respects reduced-motion preference
- Custode / Studioso / Cartografo / Codicologo roles, with deterministic V1 behavior
- Source/licensing/methodology page

## Build and tests

```bash
python build_quran.py
python test_quran.py
node --check docs/assets/app.js
node --check docs/assets/reader.js
```

Expected test result: `ALL TESTS PASSED`.

## Important limitation
No Italian copyrighted translation is included. The Italian concept index is a convenience retrieval layer and must not be presented as a translation of the Quran.
