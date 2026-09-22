# -*- coding: utf-8 -*-
"""为剩余词条（index>=230）重建 6 大批，供高效子代理处理"""
import os, json, math
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v3.json'), encoding='utf-8'))
rest = terms[230:]
outd = os.path.join(ROOT, 'data', 'llm_batches2'); os.makedirs(outd, exist_ok=True)
N = 6
per = math.ceil(len(rest) / N)
for i in range(N):
    b = rest[i * per:(i + 1) * per]
    if not b:
        continue
    json.dump([{'no': t['no'], 'head': t['head'], 'body': t['body']} for t in b],
              open(os.path.join(outd, f'rem_{i}.json'), 'w', encoding='utf-8'),
              ensure_ascii=False, indent=0)
    print(f'rem_{i}.json: {len(b)} 条  {b[0]["no"]}..{b[-1]["no"]}')
print('总剩余', len(rest))
