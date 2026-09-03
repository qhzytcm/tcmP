# -*- coding: utf-8 -*-
"""统计 HDNJ 各篇: 行数/音频时长/理解条目数"""
import pandas as pd
import re

X = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
xl = pd.ExcelFile(X)

def hms(s):
    """00:00:00,000 -> 秒"""
    m = re.match(r'(\d+):(\d+):(\d+)', str(s))
    if not m:
        return None
    h, mi, sec = map(int, m.groups())
    return h * 3600 + mi * 60 + sec

rows = []
for sn in xl.sheet_names:
    if sn == '0目录':
        continue
    df = xl.parse(sn)
    # 音频时长 = 最后结束时间
    last_end = None
    for v in df['结束时间'].dropna():
        s = hms(v)
        if s is not None:
            last_end = s
    # 理解条目
    n_und = 0
    n_orig = 0
    n_note = 0
    for v in df['文本内容'].dropna():
        t = str(v)
        if t.startswith('理解-'):
            n_und += 1
        elif t.startswith('原文-'):
            n_orig += 1
        elif t.startswith('注释-'):
            n_note += 1
    dur = f'{int(last_end//60)}分{int(last_end%60)}秒' if last_end else '-'
    rows.append((sn, len(df), dur, n_und, n_orig, n_note))

total_und = sum(r[3] for r in rows)
print(f'{"篇":<14}{"行数":<7}{"时长":<12}{"理解":<5}{"原文":<5}{"注释":<5}')
print('-' * 52)
for r in rows:
    print(f'{r[0]:<14}{r[1]:<7}{r[2]:<12}{r[3]:<5}{r[4]:<5}{r[5]:<5}')
print(f'--- 篇数: {len(rows)}, 理解条目总数: {total_und} ---')
