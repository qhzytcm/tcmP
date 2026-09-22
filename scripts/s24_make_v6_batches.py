# -*- coding: utf-8 -*-
"""S24 为「V6 现代汉语简洁化」切批（源 data/bingyuan_terms_v7.json）"""
import os, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v7.json'), encoding='utf-8'))
outd = os.path.join(ROOT, 'data', 'v6_batches'); os.makedirs(outd, exist_ok=True)
N = 6
per = math.ceil(len(terms) / N)
for i in range(N):
    b = terms[i * per:(i + 1) * per]
    if not b:
        continue
    json.dump([{'no': t['no'], 'head': t['head'], 'body': t.get('body') or ''} for t in b],
              open(os.path.join(outd, f'v6b_{i}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'v6b_{i}.json: {len(b)} 条 {b[0]["no"]}..{b[-1]["no"]}')
