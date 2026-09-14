#!/usr/bin/env python3
import json, re
from pathlib import Path
ROOT=Path(__file__).parent; DATA=ROOT/'docs/data'

def norm(s):
    return re.sub(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]','',s).replace('إ','ا').replace('أ','ا').replace('آ','ا').replace('ٱ','ا').replace('ى','ي').replace('ؤ','و').replace('ئ','ي').replace('ة','ه').lower()

def main():
    files=sorted(DATA.glob('[0-9]*.json'),key=lambda p:int(p.stem)); assert len(files)==114
    verses=[]; refs=set(); total=0
    for p in files:
        d=json.loads(p.read_text(encoding='utf8')); sid=int(p.stem); assert d['id']==sid
        for a in d['ayas']:
            r=f'{sid}:{a["v"]}'; assert r not in refs; refs.add(r); verses.append(a); total+=1
    assert total==6236, total
    byref={f'{p.stem}:{a["v"]}':a for p in files for a in json.loads(p.read_text(encoding='utf8'))['ayas']}
    for r in ['1:1','1:2','2:255','36:1','112:1','114:6']: assert r in byref
    texts=[a['text'] for a in byref.values()]
    for q in ['الله','الرحمن','رحمة','كتاب','خلق']: assert any(norm(q) in norm(t) for t in texts), q
    idx=json.loads((DATA/'index.json').read_text(encoding='utf8')); assert len(idx)==6236
    roots=json.loads((DATA/'roots.json').read_text(encoding='utf8')); lemmas=json.loads((DATA/'lemmas.json').read_text(encoding='utf8'))
    assert 'smw' in roots and 'ktb' in roots
    assert '{ll~ah' in lemmas
    concepts=json.loads((DATA/'concepts.json').read_text(encoding='utf8')); assert 'misericordia' in concepts and 'rHm' in concepts['misericordia']
    assert any(rHm_ref in refs for rHm_ref in roots['rHm']['refs'] for refs in [roots['rHm']['refs']])
    morph=(ROOT/'data/quranic-corpus-morphology-0.4.txt').read_text(encoding='utf8')
    assert 'LOCATION\tFORM\tTAG\tFEATURES' in morph and '(1:1:1:1)' in morph
    print('ALL TESTS PASSED')
if __name__=='__main__': main()
