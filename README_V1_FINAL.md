# Sacred Texts Library — Quran V1 Final Candidate

Questa build è stata ricostruita sul pacchetto del progetto fornito in chat. Il perimetro è esclusivamente il Corano.

## Correzioni principali
- Ricerca client-side resa indipendente dal caricamento simultaneo di tutti gli indici morfologici.
- Indice testuale precalcolato con campo normalizzato `q` per ricerca araba rapida e deterministica.
- Indici `roots.json` e `lemmas.json` caricati solo quando richiesti.
- Ricerca per riferimento (`1:1`, `2:255`, `114:6`).
- Ricerca per nome di sura (es. `Al-Fatiha`, `Ya-Sin`).
- Ricerca per radice con alias comuni (`r-h-m` → `rHm`, `kh-l-q` → `xlq`).
- Indice concettuale italiano esplicito: `misericordia` non è una traduzione, ma un collegamento deterministico a radici del corpus.
- Lettore con URL permanenti, morfologia parola-per-parola, copia, TTS del dispositivo, note e segnalibri locali.
- Intro cinematografica CSS 3D, saltibile e compatibile con `prefers-reduced-motion`.
- Quattro figure con funzioni V1 dichiarate senza simulare capacità non disponibili.
- Service worker v4: HTML e JSON sono network-first, con fallback offline; le vecchie cache `sacred-quran-*` vengono eliminate.
- Asset con cache-busting `?v=4` per evitare di riproporre la vecchia interfaccia.

## Verifiche eseguite
- `python build_quran.py` → OK: 114 sure, 6.236 versetti, 1.642 radici, 4.832 lemmi.
- `python test_quran.py` → `ALL TESTS PASSED`.
- `node --check docs/assets/app.js` → OK.
- `node --check docs/assets/reader.js` → OK.
- `node --check docs/sw.js` → OK.
- Server statico locale: tutti gli endpoint principali HTML/JS/CSS/JSON hanno risposto HTTP 200.
- Verifica dati ricerca: `الله` → 1.746 versetti; `رحمة` → 75; `misericordia` → 313 riferimenti; `rHm` → 313; `xlq` → 218.
- Riferimenti verificati: `1:1`, `2:255`, `114:6`.
- Morfologia: 77.429 parole con segmenti morfologici presenti nei dati distribuiti.

## Fonti
Il pacchetto conserva il materiale Uthmani e `quranic-corpus-morphology-0.4.txt` già forniti con il progetto. Consultare `docs/about.html` prima della distribuzione pubblica.

## Build
```bash
python build_quran.py
python test_quran.py
node --check docs/assets/app.js
node --check docs/assets/reader.js
node --check docs/sw.js
```

La build deve essere considerata pubblicabile solo se tutti i comandi terminano con esito positivo.
