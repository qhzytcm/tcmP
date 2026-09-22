# -*- coding: utf-8 -*-
"""S78 讹字普查：用户例 + 同类型形近讹字 + 正文残留括号"""
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
texts = [clean_noise((outs[i]['out'] if (i in outs and outs[i].get('ok')) else u['body'])) for i, u in enumerate(U)]
FULL = ''.join(texts)
print('清理后正文:', len(FULL), '字')

print('\n=== ① 用户给的例子 ===')
for a in ('塞气收', '热气泄', '气呢', '半身不送', '半身不途', '牛身不'):
    print(f'  {a}: {FULL.count(a)}')

print('\n=== ② 同类形近讹字候选（气/寒·送/遂·呃/呢·等）===')
for a in ('气呢', '气逆', '气逆上', '塞气', '寒气', '半身不送', '半身不遂', '半身不',
          '不送', '不遂', '呢逆', '呃逆', '逆上气'):
    print(f'  {a}: {FULL.count(a)}')

print('\n=== ③ 正文残留括号 ===')
for a in ('】', '【', ']', '[', '）', '（'):
    print(f'  {a!r}: {FULL.count(a)}')
hit = [(i, U[i]['name']) for i, t in enumerate(texts) if '】' in t or '】' in t or '【' in t]
print(f'  含括号的单元: {len(hit)} / {len(U)} | 样本: {hit[:10]}')
print('\n=== ④ 含『】』的单元样例 ===')
n = 0
for i, t in enumerate(texts):
    if '】' in t or '【' in t:
        n += 1
        if n <= 6:
            j = min(t.find('】'), t.find('【')) if ('】' in t or '【' in t) else -1
            print(f'  idx{i} 【{U[i]["name"]}】…{t[max(0,j-30):j+30]}…')
