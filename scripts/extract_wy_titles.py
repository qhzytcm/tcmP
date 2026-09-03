# -*- coding: utf-8 -*-
"""提取 wy01-wy30 每集 Hermes Agent 独到注释标题"""
import pandas as pd

X = r'C:\Users\DELL\Desktop\武夷山(1).xlsx'
xl = pd.ExcelFile(X)
for i in range(1, 31):
    sn = f'wy{i:02d}'
    if sn not in xl.sheet_names:
        continue
    df = xl.parse(sn)
    # 找 Hermes Agent 独到注释后的第一条（含标题）
    title = ''
    for v in df['文本内容'].dropna():
        t = str(v)
        if t.startswith('一、'):
            title = t[:50]
            break
    # 目录标题
    cat = ''
    try:
        cdf = xl.parse('0目录')
        cat = str(cdf.iloc[i - 1, 1])[:30] if i <= len(cdf) else ''
    except Exception:
        pass
    print(f'{sn} [{cat}]: {title}')
