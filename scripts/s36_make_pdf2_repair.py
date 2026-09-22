# -*- coding: utf-8 -*-
"""
S36 组装「第二份 PDF 定向提取」载荷
对已定位的残条：导出其源页的**列聚类阅读序文本**（保留原文，供 LLM 提取）
输出 data/pdf2_repair.json
"""
import os, json, re, sys
import opencc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from s35b_extract_pdf2 import ordered_lines
t2s = opencc.OpenCC('t2s')
loc = json.load(open(os.path.join(ROOT, 'dist', 'pdf2_locate.json'), encoding='utf-8'))
v12 = {t['no']: t for t in json.load(open(os.path.join(ROOT, 'data', 'bingyuan_terms_v12.json'), encoding='utf-8'))}

payload = []
for no, v in sorted(loc.items()):
    if not v['pages']:
        continue
    pgs = v['pages'][:2]
    chunks = []
    for pg in pgs:
        ls = ordered_lines(pg)
        if ls:
            chunks.append(' '.join(ls))
    src = t2s.convert(re.sub(r'[\s\u3000]+', '', ' '.join(chunks)))[:3000]
    payload.append({'no': no, 'head': v['head'], 'keys': v['keys'],
                    'cur_body': (v12[no].get('body') or ''), 'pages': pgs, 'source': src})
json.dump(payload, open(os.path.join(ROOT, 'data', 'pdf2_repair.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print(f'载荷 {len(payload)} 条')
for p in payload[:5]:
    print(f"  {p['no']} {p['head'][:12]} p{p['pages']} 源文 {len(p['source'])} 字")
print('未定位(无源文):', [no for no, v in loc.items() if not v['pages']])
