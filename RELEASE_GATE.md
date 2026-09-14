# FINAL RELEASE GATE — Quran V1

Eseguire dal root del repository:

## Sintassi
- `node --check docs/assets/app.js`
- `node --check docs/assets/reader.js`

## Build/dati esistenti
- `python build_quran.py`
- `python test_quran.py`
- `python test_release.py`

## Smoke test obbligatorio browser
Servire `docs/` con un server HTTP locale, poi verificare:

1. `/reader.html?surah=1`
   - titolo Al-Fatihah
   - select Sura popolato con 114 voci
   - 7 versetti visibili

2. `/reader.html?surah=2`
   - Al-Baqarah
   - 286 versetti

3. `/reader.html?ref=2:255`
   - apertura diretta
   - scroll automatico al versetto 255

4. Vai al versetto:
   - valore valido
   - valore non valido non rompe la pagina

5. Morfologia:
   - click/tap su una parola annotata apre il dialogo

6. Copia / Ascolta / Nota / Segna:
   - nessun errore JS
   - dati locali persistono dopo refresh

7. A− / A+ / Tema:
   - funzionano dopo refresh

8. Navigazione:
   - Sura precedente/successiva
   - ultima Sura 114
   - ritorno Biblioteca

9. Ricerca:
   - `2:255`
   - nome sura
   - testo arabo
   - radice/lemma se presenti nel corpus

10. Service Worker:
   - cache v6 attiva
   - dopo un nuovo deploy gli asset v6 vengono aggiornati
   - i JSON sono network-first

## GitHub Pages
Dopo il push:
- aprire una finestra privata
- verificare `/reader.html?surah=1`
- verificare `/reader.html?ref=2:255`
- verificare una Sura alta, ad esempio 114
- fare un hard refresh solo se il browser ha ancora una cache precedente.

Il release è FINAL solo se tutti i punti sopra passano.
