# -*- coding: utf-8 -*-
"""把 v3 词条切成分批文件，供 LLM 子代理处理"""
import os, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v3.json'), encoding='utf-8'))
outd = os.path.join(ROOT, 'data', 'llm_batches'); os.makedirs(outd, exist_ok=True)
N = 16
per = math.ceil(len(terms) / N)
n = 0
for i in range(N):
    b = terms[i * per:(i + 1) * per]
    if not b:
        continue
    json.dump([{'no': t['no'], 'head': t['head'], 'body': t['body']} for t in b],
              open(os.path.join(outd, f'batch_{i:02d}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    n += 1
print(f'切批完成: {n} 批, 每批约 {per} 条, 总 {len(terms)}')
