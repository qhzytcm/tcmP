# -*- coding: utf-8 -*-
"""调试素问3 段6 build_talk（定位兜底失效）"""
import re
import sys
from pathlib import Path

import pandas as pd

sys.path.insert(0, r'C:\Users\DELL\tcmP\scripts')
from batch_suwen import clean_part

df = pd.read_excel(r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls', sheet_name='3-生气通天论')
notes, unds, summary = [], [], ''
for v in df['文本内容'].dropna():
    t = str(v).strip()
    if t.startswith('注释-'):
        notes.append(t[3:].strip())
    elif t.startswith('理解-'):
        unds.append(t[3:].strip())
    elif t.startswith('总结-'):
        summary = t[3:].strip()

kws = ['精则养神', '柔则养筋']
# 模拟 build_talk
parts = []
for n in notes:
    if n.startswith('Hermes独立理解'):
        continue
    if any(k in n for k in kws) and len(n) > 14:
        parts.append(clean_part(n))
parts += [clean_part(u) for u in unds if len(u) > 6 and any(k in u for k in kws)]
for sp in re.split(r'[①②③④⑤⑥⑦]', summary):
    if any(k in sp for k in kws) and len(sp) > 12:
        parts.append(clean_part(sp.strip()))
print('匹配 parts:', len(parts))
for p in parts[:5]:
    print('  -', p[:60])
seen, out = [], []
for p in parts:
    if not p:
        continue
    if any(p == q or (len(p) > 20 and (p in q or q in p)) for q in seen):
        continue
    seen.append(p)
    out.append(p)
talk = '。'.join(out)
print('talk len:', len(talk), '->', talk[:80])
if len(talk) < 40:
    print('兜底执行: 总结分段:')
    for sp in re.split(r'[①②③④⑤⑥⑦]', summary):
        sp2 = clean_part(sp.strip())
        print('   len', len(sp2), ':', sp2[:50])
