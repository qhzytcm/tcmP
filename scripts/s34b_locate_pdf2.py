# -*- coding: utf-8 -*-
"""
S34b 在第二份 PDF 的 OCR 结果中定位 33 条残条（**繁简混排 → 统一 t2s 归一后检索**）
输出 dist/pdf2_locate.json
"""
import os, json, glob, re
import opencc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RES = os.path.join(ROOT, 'data', 'bingyuan2_ocr')
t2s = opencc.OpenCC('t2s')
v12 = {t['no']: t for t in json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v12.json'), encoding='utf-8'))}
TARGETS = sorted([t for t in v12.values() if len(t.get('body') or '') < 20], key=lambda t: t['no'])

pages = {}
for p in sorted(glob.glob(os.path.join(RES, '*.json'))):
    d = json.load(open(p, encoding='utf-8'))
    pages[d['page']] = t2s.convert(re.sub(r'[\s\u3000]', '', ' '.join(L['text'] for L in d['lines'])))

out = {}
for t in TARGETS:
    h = t['head']
    keys = []
    if '【' in h:
        a, _, b = h.partition('【')
        keys += [a.strip(), b.strip('】').strip()]
    keys += [h, h[:4], h[:3], h[:2]]
    keys = [k for k in dict.fromkeys(keys) if len(k) >= 2]
    hits = []; how = ''
    for k in keys:
        bodylike = [pg for pg, txt in pages.items() if txt.count('【') >= 2]
        if len(k) <= 2:
            h2 = [pg for pg, txt in pages.items() if f'【{k}】' in txt] or [pg for pg in bodylike if k in pages[pg]]
        else:
            h2 = [pg for pg, txt in pages.items() if f'【{k}】' in txt] or [pg for pg in bodylike if k in pages[pg]]
        if h2:
            hits, how = h2, f'key:{k}'
            break
    out[t['no']] = {'head': h, 'keys': keys, 'pages': sorted(hits)[:8], 'how': how}
    if hits:
        print(f"  ✓ {t['no']} {h[:18]} → 页 {sorted(hits)[:8]} ({how})")
print(f"\n已定位 {sum(1 for v in out.values() if v['pages'])} / {len(TARGETS)}")
print('未定位:', [v['head'] for v in out.values() if not v['pages']])
json.dump(out, open(os.path.join(ROOT, 'dist', 'pdf2_locate.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=1)
