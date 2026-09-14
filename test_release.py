#!/usr/bin/env python3
"""Final release gate for the static Quran web application."""
from pathlib import Path
import json,re,unicodedata
ROOT=Path(__file__).parent; DOCS=ROOT/'docs'; DATA=DOCS/'data'
DIACRITICS=re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]')
def norm(s):
 x=DIACRITICS.sub('',unicodedata.normalize('NFD',str(s or '')))
 return unicodedata.normalize('NFC',x.replace('إ','ا').replace('أ','ا').replace('آ','ا').replace('ٱ','ا').replace('ى','ي').replace('ؤ','و').replace('ئ','ي').replace('ة','ه').lower())
idx=json.loads((DATA/'index.json').read_text(encoding='utf-8')); roots=json.loads((DATA/'roots.json').read_text(encoding='utf-8')); lemmas=json.loads((DATA/'lemmas.json').read_text(encoding='utf-8')); concepts=json.loads((DATA/'concepts.json').read_text(encoding='utf-8'))
assert len(idx)==6236 and len({x['r'] for x in idx})==6236
assert {f'{s}:{v}' for s,v in [(1,1),(2,255),(114,6)]} <= {x['r'] for x in idx}
assert len({x['s'] for x in idx})==114
assert sum(x['s']==1 for x in idx)==7 and sum(x['s']==114 for x in idx)==6
assert any(norm('الله') in x['q'] for x in idx)
assert any(norm('رحمة') in x['q'] for x in idx)
assert roots.get('rHm',{}).get('refs') and roots.get('xlq',{}).get('refs')
assert lemmas and concepts.get('misericordia')==['rHm']
assert set(concepts['misericordia']) <= set(roots)
for s in range(1,115): assert (DATA/f'{s}.json').exists()
for f in ['index.html','reader.html','about.html','sw.js','manifest.webmanifest']: assert (DOCS/f).exists()
for f in ['app.css','app.js','reader.js','icon-192.png','icon-512.png']: assert (DOCS/'assets'/f).exists()
html=(DOCS/'index.html').read_text(encoding='utf-8'); app=(DOCS/'assets/app.js').read_text(encoding='utf-8'); reader=(DOCS/'assets/reader.js').read_text(encoding='utf-8'); sw=(DOCS/'sw.js').read_text(encoding='utf-8')
for token in ['Entra senza introduzione','door-left','door-right','keeperBtn','searchForm','suraGrid']: assert token in html, token
for token in ['index.json','roots.json','lemmas.json','concepts.json','reader.html?ref=','rHm']: assert token in app, token
for token in ['data/${surah}.json','showMorph','quran-bookmarks','quran-notes','speechSynthesis']: assert token in reader, token
assert "sacred-quran-v5" in sw and 'no-store' in sw and 'clients.claim' in sw
print('FINAL RELEASE GATE: ALL TESTS PASSED')
