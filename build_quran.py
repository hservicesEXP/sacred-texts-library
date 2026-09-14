#!/usr/bin/env python3
"""Reproducible static build/validation for Sacred Texts Library — Quran V1."""
from pathlib import Path
import json, re, shutil, unicodedata

ROOT = Path(__file__).parent
DOCS = ROOT / 'docs'
DATA = DOCS / 'data'
SOURCE_MORPH = ROOT / 'data' / 'quranic-corpus-morphology-0.4.txt'
VERSION = '4'

DIACRITICS = re.compile(r'[\u064B-\u065F\u0670\u06D6-\u06ED\u0640]')

def norm_arabic(s: str) -> str:
    x = DIACRITICS.sub('', unicodedata.normalize('NFD', str(s or '')))
    x = (x.replace('إ','ا').replace('أ','ا').replace('آ','ا').replace('ٱ','ا')
           .replace('ى','ي').replace('ؤ','و').replace('ئ','ي').replace('ة','ه').lower())
    return unicodedata.normalize('NFC', x)

def main():
    files = sorted(DATA.glob('[0-9]*.json'), key=lambda p: int(p.stem))
    assert len(files) == 114, f'Sure trovate: {len(files)}'
    rows, seen = [], set()
    surah_meta = []
    total = 0
    for p in files:
        sid = int(p.stem)
        d = json.loads(p.read_text(encoding='utf-8'))
        assert d.get('id') == sid and isinstance(d.get('ayas'), list) and d['ayas'], p
        ayas = d['ayas']
        refs_in_sura = set()
        for a in ayas:
            assert isinstance(a.get('v'), int) and a['v'] >= 1, f'Versetto invalido {p}'
            ref = f'{sid}:{a["v"]}'
            assert ref not in seen, f'Duplicato {ref}'
            seen.add(ref); refs_in_sura.add(ref)
            text = a.get('text','')
            assert text.strip(), f'Testo mancante {ref}'
            rows.append({'r': ref, 's': sid, 'v': a['v'], 'n': d.get('name',''), 't': text, 'q': norm_arabic(text)})
        assert len(refs_in_sura) == len(ayas)
        surah_meta.append({'s': sid, 'n': d.get('name',''), 'v': len(ayas)})
        total += len(ayas)

    assert total == 6236, f'Numero versetti inatteso: {total}'
    assert seen == {f'{s}:{v}' for s, m in enumerate(surah_meta, 1) for v in range(1, m['v'] + 1)}
    (DATA/'index.json').write_text(json.dumps(rows, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (DATA/'surahs.json').write_text(json.dumps(surah_meta, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    roots, lemmas = {}, {}
    for p in files:
        d = json.loads(p.read_text(encoding='utf-8'))
        for a in d['ayas']:
            ref = f'{d["id"]}:{a["v"]}'
            for w in a.get('words', []):
                for seg in w.get('segments', []):
                    root = seg.get('root')
                    lemma = seg.get('lemma')
                    if root:
                        roots.setdefault(root, {'refs': []})['refs'].append(ref)
                    if lemma:
                        lemmas.setdefault(lemma, []).append(ref)
    for v in roots.values(): v['refs'] = sorted(set(v['refs']))
    for k in lemmas: lemmas[k] = sorted(set(lemmas[k]))
    (DATA/'roots.json').write_text(json.dumps(roots, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')
    (DATA/'lemmas.json').write_text(json.dumps(lemmas, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

    concepts_path = DATA/'concepts.json'
    concepts = json.loads(concepts_path.read_text(encoding='utf-8')) if concepts_path.exists() else {}
    assert isinstance(concepts, dict)
    assert 'misericordia' in concepts and concepts['misericordia'], 'Concetto italiano misericordia mancante'
    for concept, keys in concepts.items():
        assert isinstance(concept, str) and isinstance(keys, list)
        for key in keys: assert key in roots, f'Concetto {concept}: radice {key} assente nel corpus'

    assert SOURCE_MORPH.exists(), 'quranic-corpus-morphology-0.4.txt mancante'
    print(f'BUILD OK · {len(files)} sure · {total} versetti · {len(roots)} radici · {len(lemmas)} lemmi · indice v{VERSION}')
    return 0

if __name__ == '__main__':
    raise SystemExit(main())
