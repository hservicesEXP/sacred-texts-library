# Sacred Texts Library — Quran Final Candidate

Questa build contiene esclusivamente il Corano.

## Release gate

- 114 sure
- 6.236 versetti
- indice testuale statico
- indici radici e lemmi
- concetti italiani presenti nel dataset del progetto
- lettore RTL
- riferimenti permanenti `reader.html?ref=sura:ayat`
- morfologia interattiva dove il corpus la fornisce
- note e segnalibri in localStorage
- copia testo
- TTS tramite Web Speech API quando disponibile sul dispositivo
- PWA con cache versionata `sacred-quran-v5`
- ingresso 3D CSS lazy/non obbligatorio e saltibile
- quattro figure della biblioteca con funzioni dichiarate esplicitamente

## Build

```bash
python build_quran.py
python test_quran.py
python test_release.py
node --check docs/assets/app.js
node --check docs/assets/reader.js
```

La build deve essere considerata pubblicabile solo se tutti i comandi terminano con successo.

## Deploy

Pubblicare esclusivamente `docs/` su GitHub Pages. Non aggiungere altri corpora in questa milestone.
