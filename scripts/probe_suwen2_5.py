# -*- coding: utf-8 -*-
"""查 HDNJ 素问 2-5 篇 sheet + 原文短句预览（定义十段用）"""
import pandas as pd

X = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
xl = pd.ExcelFile(X)

# 找素问 2-5 篇 sheet（命名篇中: 四气调神/生气通天/金匮真言/阴阳应象）
cands = [s for s in xl.sheet_names if any(k in s for k in
         ('四气调神', '生气通天', '金匮真言', '阴阳应象', '素问'))]
print('候选 sheets:', cands[:10])

targets = {}
for sn in xl.sheet_names:
    if '四气调神' in sn or '生气通天' in sn or '金匮真言' in sn or '阴阳应象' in sn:
        df = xl.parse(sn)
        orig = [str(v).strip()[3:] for v in df['文本内容'].dropna()
                if str(v).strip().startswith('原文-')]
        targets[sn] = orig
        print(f'\n===== {sn}（原文短句 {len(orig)} 条）=====')
        for s in orig[:22]:
            print('  ', s[:46])
