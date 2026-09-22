# -*- coding: utf-8 -*-
"""
S31 从语料矿掘「中药名 OCR 变体」，用**高频真药名**作纠错目标（强证据）
输出候选对照表（先审后改）：dist/herb_variants.json
"""
import json, os, re
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DOSE = '一两三四五六七八九十钱分斤勺厘'
RX = re.compile(r'([\u4e00-\u9fff]{2,3})各?(?=[' + DOSE + r'])')
terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v11.json'), encoding='utf-8'))
cnt = Counter()
for t in terms:
    for m in RX.finditer(t.get('body') or ''):
        cnt[m.group(1)] += 1
HERB = {w for w, n in cnt.items() if n >= 60}          # 高频 → 真药名
print('高频药名(≥60次):', len(HERB))
print('  样例:', sorted(HERB, key=lambda w: -cnt[w])[:25])
# 1 字差的候选
prop = {}
for g, n in cnt.items():
    if g in HERB or n < 3:
        continue
    cands = [h for h in HERB if len(h) == len(g) and sum(1 for x, y in zip(g, h) if x != y) == 1
             and sorted(g) != sorted(h)]
    if cands:
        h = max(cands, key=lambda x: cnt[x])
        prop[g] = {'to': h, 'freq_g': n, 'freq_h': cnt[h]}
print(f'\n候选纠错对: {len(prop)}')
for g, v in sorted(prop.items(), key=lambda kv: -kv[1]['freq_g'])[:40]:
    print(f"  {g}({v['freq_g']}) → {v['to']}({v['freq_h']})")
json.dump(prop, open(os.path.join(ROOT, 'dist', 'herb_variants.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
