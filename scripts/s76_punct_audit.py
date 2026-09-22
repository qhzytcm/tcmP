# -*- coding: utf-8 -*-
"""S76 标点覆盖率审计 + 噪声分类"""
import os, re, json
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
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
PUNCT = '，。、；：？！'
nop, few = [], []
for i, u in enumerate(U):
    r = outs.get(i)
    t = (r['out'] if (r and r.get('ok')) else u['body']) if r else u['body']
    n = sum(t.count(c) for c in PUNCT)
    if n == 0:
        nop.append(i)
    elif n / max(1, len(t)) < 0.012:      # 标点密度过低
        few.append(i)
print(f'单元 {len(U)}')
print(f'  **完全无标点**: {len(nop)}')
print(f'  标点密度<1.2%: {len(few)}')
print(f'  合计待补: {len(nop)+len(few)}')
for i in (nop + few)[:8]:
    r = outs.get(i)
    t = (r['out'] if (r and r.get('ok')) else U[i]['body']) if r else U[i]['body']
    print(f'  idx{i} 【{U[i]["name"]}】flag={"LLM" if (r and r.get("ok")) else (r.get("why") if r else "未校")}')
    print(f'      {t[:76]}')
