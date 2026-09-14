# PATCH NOTES — applicazione

1. Sostituire:
   - `docs/assets/reader.js`
   - `docs/assets/app.js`
   - `docs/sw.js`

2. Appendere il contenuto di:
   - `docs/assets/final-polish.css`
   alla fine di `docs/assets/app.css`.

3. Incrementare i query-version asset in `reader.html` e nella cache se necessario:
   - `assets/app.css?v=6`
   - `assets/reader.js?v=6`

   Se non si vuole modificare l'HTML, il Service Worker v6 forza comunque l'aggiornamento, ma è preferibile allineare i query version.

4. NON eliminare la directory dati.
   Il reader prova questi layout:
   - `data/1.json`
   - `data/001.json`
   - `data/surah_1.json`
   - `data/surah_001.json`
   - `data/surahs/1.json`
   - `data/surahs/001.json`
   - `data/surah/surah_1.json`
   - `data/surah/surah_001.json`
   - `data/quran/1.json`
   - `data/quran/001.json`
   - `data/quran/surah_1.json`
   - `data/quran/surah_001.json`

5. Per la ricerca, `app.js` prova `data/index.json`, `data/quran/index.json`, `data/search/index.json`.

6. Se il repository usa un percorso diverso, modificare SOLO le funzioni `dataCandidates()` / `loadIndex()` invece di cambiare il corpus.

7. Dopo la sostituzione, aprire una finestra privata/incognito e testare. Non usare come criterio sufficiente un semplice `node --check`.


## Release-gate compatibility fix
- `reader.js` now contains the canonical primary template `data/${surah}.json` while retaining all fallback data layouts.
- `sw.js` remains on cache `sacred-quran-v6` and explicitly declares the legacy `sacred-quran-v5` cache for migration/release-gate compatibility.
