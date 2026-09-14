#!/usr/bin/env python3
"""Release gate for the Quran V1 static corpus and search indexes."""
from pathlib import Path
import json, re, sys, unicodedata
ROOT=Path(__file__).parent; DATA=ROOT/'docs/data'
DIACRITICS=re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]')
def norm(s):
    x=DIACRITICS.sub('', unicodedata.normalize('NFD', str(s or '')))
    x=(x.replace('إ','ا').replace('أ','ا').replace('آ','ا').replace('ٱ','ا').replace('ى','ي').replace('ؤ','و').replace('ئ','ي').replace('ة','ه').lower())
    return unicodedata.normalize('NFC', x)

def main():
    idx=json.loads((DATA/'index.json').read_text(encoding='utf-8'))
    assert len(idx)==6236
    refs={x['r'] for x in idx}; assert len(refs)==6236
    assert {'1:1','2:255','114:6'} <= refs
    assert len({x['s'] for x in idx})==114
    assert all(norm('الله') in x['q'] for x in [next(r for r in idx if r['r']=='1:1')])
    assert any(norm('الله') in x['q'] for x in idx)
    assert any(norm('رحمة') in x['q'] for x in idx)
    assert any(x['s']==1 for x in idx) and sum(x['s']==1 for x in idx)==7
    assert any(x['s']==114 for x in idx) and sum(x['s']==114 for x in idx)==6
    roots=json.loads((DATA/'roots.json').read_text(encoding='utf-8'))
    lemmas=json.loads((DATA/'lemmas.json').read_text(encoding='utf-8'))
    concepts=json.loads((DATA/'concepts.json').read_text(encoding='utf-8'))
    assert 'rHm' in roots and roots['rHm']['refs']
    assert 'misericordia' in concepts and 'rHm' in concepts['misericordia']
    mercy_refs=set(roots['rHm']['refs']); assert mercy_refs, 'misericordia non produce riferimenti'
    assert any(v for v in lemmas.values())
    for s in range(1,115): assert (DATA/f'{s}.json').exists()
    print('ALL TESTS PASSED')
if __name__=='__main__':
    try: main()
    except Exception as e: print('TEST FAILED:',e); sys.exit(1)
