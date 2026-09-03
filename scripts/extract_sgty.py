# -*- coding: utf-8 -*-
"""提取 1-上古天真论 的核心内容: 原文段/理解条目/关键注释"""
import pandas as pd

X = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
df = pd.read_excel(X, sheet_name='1-上古天真论')

orig = []   # 原文段
und = []    # 理解段
note = []   # 注释段（长文本）
for v in df['文本内容'].dropna():
    t = str(v).strip()
    if t.startswith('原文-') and len(t) > 40:
        orig.append(t[3:].strip())
    elif t.startswith('理解-') and len(t) > 30:
        und.append(t[3:].strip())
    elif t.startswith('注释-') and len(t) > 120:
        note.append(t[3:].strip())

print(f'原文段: {len(orig)}, 理解: {len(und)}, 长注释: {len(note)}')
print('\n===== 原文段（前 12 条）=====')
for i, t in enumerate(orig[:12], 1):
    print(f'[{i}] {t[:120]}')
print('\n===== 理解条目（31 条, 前 10 条）=====')
for i, t in enumerate(und[:10], 1):
    print(f'[{i}] {t[:110]}')
print('\n===== 长注释（前 5 条）=====')
for i, t in enumerate(note[:5], 1):
    print(f'[{i}] {t[:130]}')
