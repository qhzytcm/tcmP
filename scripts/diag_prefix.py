# -*- coding: utf-8 -*-
"""查看 1-上古天真论 文本前缀分布"""
import pandas as pd
from collections import Counter

X = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
df = pd.read_excel(X, sheet_name='1-上古天真论')
prefixes = Counter()
samples = {}
for v in df['文本内容'].dropna():
    t = str(v).strip()
    p = t[:3]
    prefixes[p] += 1
    if p not in samples:
        samples[p] = t[:80]

print('前缀分布:', dict(prefixes.most_common(10)))
print('\n各前缀样例:')
for p, s in samples.items():
    print(f'  [{p}] {s}')
