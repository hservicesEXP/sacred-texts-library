#!/usr/bin/env python3
"""Validate/build helper for the static Quran V1. No external dependencies."""
from pathlib import Path
import json, re, shutil
ROOT=Path(__file__).parent; DOCS=ROOT/'docs'; DATA=DOCS/'data'

def main():
    files=sorted(DATA.glob('[0-9]*.json'), key=lambda p:int(p.stem))
    assert len(files)==114, f'Sure trovate: {len(files)}'
    rows=[]; total=0; seen=set()
    for p in files:
        d=json.loads(p.read_text(encoding='utf-8')); sid=int(p.stem)
        assert d.get('id')==sid and isinstance(d.get('ayas'),list), p
        assert d['ayas'], p
        for a in d['ayas']:
            ref=f'{sid}:{a["v"]}'; assert ref not in seen, f'Duplicato {ref}'; seen.add(ref); rows.append({'r':ref,'s':sid,'v':a['v'],'n':d.get('name',''),'t':a.get('text','')}); total+=1
    (DATA/'index.json').write_text(json.dumps(rows,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    roots={}; lemmas={}
    for p in files:
        d=json.loads(p.read_text(encoding='utf-8'))
        for a in d['ayas']:
            ref=f'{d["id"]}:{a["v"]}'
            for w in a.get('words',[]):
                for seg in w.get('segments',[]):
                    if seg.get('root'): roots.setdefault(seg['root'],{'ar':'','refs':[]})['refs'].append(ref)
                    if seg.get('lemma'): lemmas.setdefault(seg['lemma'],[]).append(ref)
    for v in roots.values(): v['refs']=sorted(set(v['refs']))
    for k,v in lemmas.items(): lemmas[k]=sorted(set(v))
    (DATA/'roots.json').write_text(json.dumps(roots,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    (DATA/'lemmas.json').write_text(json.dumps(lemmas,ensure_ascii=False,separators=(',',':')),encoding='utf-8')
    print(f'OK: {len(files)} sure, {total} versetti, {len(roots)} radici, {len(lemmas)} lemmi')
    return 0
if __name__=='__main__': raise SystemExit(main())
