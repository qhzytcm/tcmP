# -*- coding: utf-8 -*-
"""提取 1-上古天真论: 原文段(短句合并)/理解条目/总结"""
import pandas as pd

X = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
df = pd.read_excel(X, sheet_name='1-上古天真论')

orig, und, summary = [], [], ''
for v in df['文本内容'].dropna():
    t = str(v).strip()
    if t.startswith('原文-'):
        orig.append(t[3:].strip())
    elif t.startswith('理解-'):
        und.append(t[3:].strip())
    elif t.startswith('总结-'):
        summary = t[3:].strip()

print(f'原文短句: {len(orig)}, 理解: {len(und)}')
print('\n===== 原文（合并为段落, 前 60 句）=====')
for i, t in enumerate(orig[:60], 1):
    print(f'{i}. {t[:80]}')
print('\n===== 理解条目（全部）=====')
for i, t in enumerate(und, 1):
    print(f'[{i}] {t[:100]}')
print('\n===== 总结 =====')
print(summary[:600])
