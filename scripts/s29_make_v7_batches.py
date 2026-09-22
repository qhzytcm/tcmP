# -*- coding: utf-8 -*-
"""S29 为「V7 中医病因辨证校正」切批（源 data/bingyuan_terms_v10.json）"""
import os, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SRC = 'bingyuan_terms_v10.json'
terms = json.load(open(os.path.join(ROOT, 'data', SRC), encoding='utf-8'))
outd = os.path.join(ROOT, 'data', 'v7_batches'); os.makedirs(outd, exist_ok=True)
N = 6
per = math.ceil(len(terms) / N)
for i in range(N):
    b = terms[i * per:(i + 1) * per]
    if not b:
        continue
    json.dump([{'no': t['no'], 'head': t['head'], 'body': t.get('body') or ''} for t in b],
              open(os.path.join(outd, f'v7b_{i}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'v7b_{i}.json: {len(b)} 条 {b[0]["no"]}..{b[-1]["no"]}')
