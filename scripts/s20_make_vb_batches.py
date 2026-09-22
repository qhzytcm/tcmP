# -*- coding: utf-8 -*-
"""
S20 为「V4 补缺重构」切批 + 缺项画像（基线）
输入 data/bingyuan_terms_v5.json（= 桌面 病源辞典V3.docx 的内容）
输出 data/vb_batches/vb_{0..5}.json + dist/v4_gap_baseline.json
"""
import os, re, json, math
from collections import Counter
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIST = os.path.join(ROOT, 'dist'); os.makedirs(DIST, exist_ok=True)

SRC_RE = r'[病满润游漏瑞烤浏消荆房痛]源'
ZH_RE = r'病[状默送肤选迭达跋然]'
ZHI_RE = r'[治洛活浩照浴跆沼陪邵路阁]法'
MARK = re.compile(f'({SRC_RE})|({ZH_RE})|({ZHI_RE})')
RX_THERAPY = re.compile(r'宜|用|服|方|汤|散|丸|膏|灸|针|外治|敷|洗|涂|参看|参见|忌')

terms = json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v5.json'), encoding='utf-8'))
stat = Counter()
for t in terms:
    b = t.get('body') or ''
    has = {'病源': bool(re.search(SRC_RE, b)), '病状': bool(re.search(ZH_RE, b)),
           '治法': bool(re.search(ZHI_RE, b))}
    for k, v in has.items():
        if v:
            stat[k] += 1
    if all(has.values()):
        stat['三要素齐备'] += 1
    if not RX_THERAPY.search(b):
        stat['无治疗特征词'] += 1
    if len(b) < 20:
        stat['过短(<20字)'] += 1
n = len(terms)
cov = {k: f'{stat[k]} ({100*stat[k]/n:.1f}%)' for k in ('病源', '病状', '治法', '三要素齐备', '无治疗特征词', '过短(<20字)')}
print('缺项基线:', cov)

outd = os.path.join(ROOT, 'data', 'vb_batches'); os.makedirs(outd, exist_ok=True)
N = 6
per = math.ceil(n / N)
for i in range(N):
    b = terms[i * per:(i + 1) * per]
    if not b:
        continue
    json.dump([{'no': t['no'], 'head': t['head'], 'body': t['body']} for t in b],
              open(os.path.join(outd, f'vb_{i}.json'), 'w', encoding='utf-8'), ensure_ascii=False, indent=0)
    print(f'vb_{i}.json: {len(b)} 条 {b[0]["no"]}..{b[-1]["no"]}')
json.dump({'coverage': cov, 'n': n}, open(os.path.join(DIST, 'v4_gap_baseline.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
