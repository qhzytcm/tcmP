# -*- coding: utf-8 -*-
"""
S18 为「上下文重构」切批（段=词条），供并行 LLM 子代理逐段重构
输入 data/bingyuan_terms_v4.json（已 LLM 矫正+语义群标点）
输出 data/rb_batches/rb_{0..5}.json（每批~267条）
"""
import os, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v4.json'), encoding='utf-8'))
outd = os.path.join(ROOT, 'data', 'rb_batches'); os.makedirs(outd, exist_ok=True)
N = 6
per = math.ceil(len(terms) / N)
for i in range(N):
    b = terms[i * per:(i + 1) * per]
    if not b:
        continue
    json.dump([{'no': t['no'], 'head': t['head'], 'body': t['body']} for t in b],
              open(os.path.join(outd, f'rb_{i}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    print(f'rb_{i}.json: {len(b)} 条  {b[0]["no"]}..{b[-1]["no"]}')
print('总', len(terms))
