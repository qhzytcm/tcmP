# -*- coding: utf-8 -*-
"""查素问 6-10 篇 sheet + 原文短句预览"""
import pandas as pd

X = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
xl = pd.ExcelFile(X)

cands = [s for s in xl.sheet_names if any(k in s for k in
         ('阴阳离合', '阴阳别', '灵兰秘典', '六节藏象', '五藏生成', '玉版'))]
print('候选:', cands)

targets = {}
for sn in xl.sheet_names:
    if any(k in sn for k in ('阴阳离合', '阴阳别', '灵兰秘典', '六节藏象', '五藏生成')):
        df = xl.parse(sn)
        orig = [str(v).strip()[3:] for v in df['文本内容'].dropna()
                if str(v).strip().startswith('原文-')]
        targets[sn] = orig
        print(f'\n===== {sn}（{len(orig)} 句）=====')
        for s in orig[:20]:
            print('  ', s[:44])
