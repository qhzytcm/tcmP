# -*- coding: utf-8 -*-
"""
S79 讹字普查（广度）：用「低频字 + 上下文」定位形近讹字
方法（本会话已验证有效）：真字高频、讹形低频；把「全书 ≤N 次且形近于高频字」者列出
"""
import os, re, json, sys
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from s77_clean import clean as clean_noise
U = json.load(open(os.path.join(ROOT, 'data', 'pdf3_units_v2.json'), encoding='utf-8'))
outs = {}
for line in open(os.path.join(ROOT, 'data', 'pdf3_llm_out.jsonl'), encoding='utf-8', errors='replace'):
    line = line.strip()
    if line:
        try:
            r = json.loads(line)
        except Exception:
            continue
        if r['i'] not in outs or (r.get('ok') and not outs[r['i']].get('ok')):
            outs[r['i']] = r
TEXTS = [clean_noise((outs[i]['out'] if (i in outs and outs[i].get('ok')) else u['body'])) for i, u in enumerate(U)]
FULL = ''.join(TEXTS)
print('正文:', len(FULL), '字')

# 低频汉字（全书出现 ≤3 次）→ 极可疑
c = Counter(ch for ch in FULL if 0x4E00 <= ord(ch) <= 0x9FFF)
rare = [(ch, n) for ch, n in c.items() if n <= 3]
print(f'低频字(≤3次): {len(rare)} 种')
print('\n=== 低频字 + 其上下文（前 46 组）===')
rows = []
for ch, n in sorted(rare, key=lambda z: z[1]):
    idxs = [m.start() for m in re.finditer(re.escape(ch), FULL)][:2]
    for k in idxs:
        rows.append((n, ch, FULL[max(0, k - 14):k + 15]))
for n, ch, ctx in rows[:46]:
    print(f'  {ch}×{n} | …{ctx}…')
