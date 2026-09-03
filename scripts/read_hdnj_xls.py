# -*- coding: utf-8 -*-
"""读取 HDNJ音频理解(2).xls 结构"""
import sys
import pandas as pd

X = r'C:\Users\DELL\Desktop\HDNJ音频理解(2).xls'
try:
    xl = pd.ExcelFile(X)
    print('sheets:', xl.sheet_names)
    for sn in xl.sheet_names:
        df = xl.parse(sn)
        print(f'--- [{sn}] 行数={len(df)} 列={list(df.columns)}')
        if len(df) > 0:
            print(df.head(3).to_string()[:900])
            print('...')
            print(df.tail(2).to_string()[:400])
except Exception as e:
    print('错误:', type(e).__name__, str(e)[:300])
