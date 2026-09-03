# -*- coding: utf-8 -*-
"""SW81 sheet 文本结构诊断"""
import pandas as pd

df = pd.read_excel(r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls', sheet_name='SW81')
from collections import Counter
c = Counter()
for v in df['文本内容'].dropna():
    t = str(v).strip()
    if t.startswith('原文-'):
        c['原文'] += 1
    elif t.startswith('注释-'):
        c['注释'] += 1
    elif t.startswith('理解-'):
        c['理解'] += 1
    elif t.startswith('总结-'):
        c['总结'] += 1
    else:
        c['其他'] += 1
print('行类型分布:', dict(c))
# 看前几行
print('\n前 12 行:')
for v in df['文本内容'].dropna().head(12):
    print('  ', str(v).strip()[:80])
