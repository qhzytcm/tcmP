# -*- coding: utf-8 -*-
"""读取 武夷山(1).xlsx 结构"""
import pandas as pd

X = r'C:\Users\DELL\Desktop\武夷山(1).xlsx'
try:
    xl = pd.ExcelFile(X)
    print('sheets:', xl.sheet_names)
    for sn in xl.sheet_names:
        df = xl.parse(sn)
        print(f'--- [{sn}] 行数={len(df)} 列={list(df.columns)}')
        # 全文预览（前 30 行）
        for i, row in df.head(30).iterrows():
            vals = [str(v)[:70] for v in row.values if str(v) != 'nan']
            if vals:
                print(f'  {i}: {" | ".join(vals)[:180]}')
        if len(df) > 30:
            print(f'  ... (共 {len(df)} 行)')
            for i, row in df.tail(3).iterrows():
                vals = [str(v)[:70] for v in row.values if str(v) != 'nan']
                if vals:
                    print(f'  {i}: {" | ".join(vals)[:180]}')
except Exception as e:
    print('错误:', type(e).__name__, str(e)[:300])
