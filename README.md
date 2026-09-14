# Quran V1 Final Repair Pack

Data di riferimento: repository `hservicesEXP/sacred-texts-library`, build web osservata il 14/09/2026.

## Problema rilevato

La `reader.html` attuale carica i dati con un solo percorso:

`data/<sura>.json`

e, se quel fetch fallisce, mostra "Impossibile caricare la sura". Il Service Worker v5 inoltre può mantenere asset vecchi.

Questo pack corregge il lato applicativo senza sostituire il corpus.

## File

- `docs/assets/reader.js` — reader robusto con ricerca di più layout dati, diagnostica, retry, local storage e service-worker migration.
- `docs/assets/app.js` — ricerca robusta e compatibile con varianti di indice/percorsi.
- `docs/sw.js` — cache v6, network-first per HTML/JS/CSS/JSON, invalidazione delle cache precedenti.
- `docs/assets/final-polish.css` — rifiniture UI. Va APPESO a `docs/assets/app.css`.
- `PATCH_NOTES.md` — ordine esatto delle operazioni.
- `RELEASE_GATE.md` — test finali da eseguire prima del deploy.

## Importante

Questo è un **repair pack/drop-in patch**, non una copia completa del repository: in questo ambiente non è stato possibile clonare il repository GitHub e non bisogna inventare o ricostruire i file dati del corpus.

Il pack NON modifica né sostituisce `data/`, `index.json`, `roots.json`, `lemmas.json`, `concepts.json` o i dati morfologici.
