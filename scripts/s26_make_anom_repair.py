# -*- coding: utf-8 -*-
"""
S26 组装「异常条目定向重建」载荷
对 14 条异常：定位源页（优先【繁体词目】标记，否则用正文特征串），
汇出源页的**列聚类阅读序繁体原文**，供 LLM 重建。
输出 data/anom_repair.json
"""
import json, os, sys, glob
import opencc
ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(ROOT, 'scripts'))
from s2_convert import page_text
cc = opencc.OpenCC('s2t')

SRC = 'bingyuan_terms_v10.json' if os.path.exists(os.path.join(ROOT, 'data', 'bingyuan_terms_v10.json')) else 'bingyuan_terms_v9.json'
_all = {t['no']: t for t in json.load(open(os.path.join(ROOT, 'data', SRC), encoding='utf-8'))}
# 自动选取：正文 <20 字（残条）或 >2500 字（超长混排）
ANOM = [t['no'] for t in _all.values() if len(t.get('body') or '') < 20 or len(t.get('body') or '') > 2500]
v8 = _all

RECS = {}
for p in sorted(glob.glob(os.path.join(ROOT, 'data', 'bingyuan_ocr', 'page_*.json'))):
    d = json.load(open(p, encoding='utf-8'))
    RECS[d['page']] = d

payload = []
for no in ANOM:
    t = v8[no]
    h, body = t['head'], (t.get('body') or '')
    ht = cc.convert(h)
    pgs = []
    for pg, rec in RECS.items():
        txt = page_text(rec)[0]
        if f'【{ht}】' in txt:
            pgs.append(pg)
    how = 'marker'
    if not pgs:                      # 退化：用较长的正文特征串定位（要求可命中）
        cands = [body[4:24], body[len(body)//2:len(body)//2 + 20], body[8:28]]
        for snip0 in cands:
            snip = cc.convert(snip0)
            if len(snip) < 8:
                continue
            hit = [pg for pg, rec in RECS.items() if snip in page_text(rec)[0]]
            if hit:
                pgs = hit
                how = 'snippet:' + snip[:16]
                break
        if not pgs:
            how = '未定位'
    pgs = sorted(set(pgs))[:3]
    src = '\n'.join(page_text(RECS[p])[0] for p in pgs) if pgs else ''
    payload.append({'no': no, 'head': h, 'cur_len': len(body), 'cur_head': body[:60],
                    'pages': pgs, 'locate': how, 'source_trad': src[:4000]})
    print(f"{no} {h} | 源页 {pgs} | 定位={how} | 源文 {len(src)} 字")
json.dump(payload, open(os.path.join(ROOT, 'data', 'anom_repair.json'), 'w', encoding='utf-8'),
          ensure_ascii=False, indent=1)
print('已写 data/anom_repair.json |', len(payload), '条')
